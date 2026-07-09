import { appendFileSync, existsSync, mkdirSync, readdirSync, statSync, writeFileSync } from "node:fs"
import { join, resolve } from "node:path"
import { spawnSync } from "node:child_process"

const COMMAND_NAME = "test-analysis-workflow"
const OUTPUT_FILE = "deliverables/test-analysis-solution.json"
const PATH_FILE = "path.txt"
const LOG_FILE = ".opencode/logs/test-analysis-output-path.log"
const START_TIME_SKEW_MS = 5000

const pending = new Map()

function safeJson(value) {
  try {
    return JSON.stringify(value)
  } catch {
    return "[unserializable]"
  }
}

function compactEvent(event) {
  const text = safeJson(event)
  return text.length > 3000 ? `${text.slice(0, 3000)}...<truncated>` : text
}

function errorInfo(error) {
  return {
    name: error?.name,
    message: error?.message || String(error),
    stack: error?.stack,
  }
}

function writeLocalLog(root, level, message, extra = {}) {
  const path = join(root, LOG_FILE)
  mkdirSync(join(root, ".opencode", "logs"), { recursive: true })
  appendFileSync(
    path,
    `${new Date().toISOString()} ${level.toUpperCase()} ${message} ${safeJson(extra)}\n`,
    "utf8",
  )
}

function findStringValue(value, keys) {
  if (!value || typeof value !== "object") return undefined
  for (const key of keys) {
    if (typeof value[key] === "string") return value[key]
  }
  for (const child of Object.values(value)) {
    const found = findStringValue(child, keys)
    if (found) return found
  }
  return undefined
}

function sessionKey(event) {
  return (
    findStringValue(event, ["sessionID", "sessionId", "session"]) ||
    "default"
  )
}

function commandName(value) {
  return findStringValue(value, ["command", "name"]) || ""
}

function safePathSegment(value) {
  return String(value || "unknown").replace(/[^A-Za-z0-9._-]/g, "_")
}

function isAnalysisCommand(value) {
  return commandName(value) === COMMAND_NAME || JSON.stringify(value).includes(COMMAND_NAME)
}

function listRunIds(root) {
  const runsDir = join(root, "outputs", "runs")
  if (!existsSync(runsDir)) return new Set()
  return new Set(
    readdirSync(runsDir, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name),
  )
}

function findCandidateRuns(root, state) {
  const runsDir = join(root, "outputs", "runs")
  if (!existsSync(runsDir)) return []

  const candidates = []
  for (const entry of readdirSync(runsDir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue
    const runDir = join(runsDir, entry.name)
    const solutionPath = join(runDir, OUTPUT_FILE)
    if (!existsSync(solutionPath)) continue

    const solutionStat = statSync(solutionPath)
    const runStat = statSync(runDir)
    const isNewRun = !state.existingRuns.has(entry.name)
    const changedAfterStart = Math.max(solutionStat.mtimeMs, runStat.mtimeMs) >= state.startTime - START_TIME_SKEW_MS
    if (!isNewRun && !changedAfterStart) continue

    candidates.push({
      runDir,
      solutionPath,
      mtimeMs: Math.max(solutionStat.mtimeMs, runStat.mtimeMs),
    })
  }

  return candidates.sort((left, right) => right.mtimeMs - left.mtimeMs)
}

function checkStagedRun(root, runDir) {
  const result = spawnSync(
    "python",
    ["bin/check-staged-run.py", runDir, "--scope", "analysis"],
    {
      cwd: root,
      encoding: "utf8",
      windowsHide: true,
    },
  )
  return {
    ok: result.status === 0,
    output: `${result.stdout || ""}${result.stderr || ""}`.trim(),
  }
}

async function log(root, client, level, message, extra = {}) {
  try {
    writeLocalLog(root, level, message, extra)
  } catch (error) {
    // Keep the hook alive even if project-local diagnostics cannot be written.
  }
  if (client?.app?.log) {
    try {
      await client.app.log({
        body: {
          service: "test-analysis-output-path",
          level,
          message,
          extra,
        },
      })
    } catch (error) {
      try {
        writeLocalLog(root, "warn", "client.app.log failed", errorInfo(error))
      } catch {
        // No-op: both log sinks failed.
      }
    }
  }
}

function deletePending(stateKey) {
  pending.delete(stateKey)
}

function writePathFile(runDir, solutionPath) {
  const absoluteSolutionPath = resolve(solutionPath)
  const runPathFile = join(runDir, PATH_FILE)
  mkdirSync(runDir, { recursive: true })
  writeFileSync(runPathFile, `${absoluteSolutionPath}\n`, "utf8")

  return {
    pathFile: runPathFile,
    solutionPath: absoluteSolutionPath,
  }
}

async function scanState(root, client, stateKey, trigger) {
  const state = pending.get(stateKey)
  if (!state) return false

  const candidates = findCandidateRuns(root, state)
  await log(root, client, "debug", "Candidate analysis runs scanned", {
    sessionKey: stateKey,
    trigger,
    candidateCount: candidates.length,
    candidates: candidates.map((candidate) => candidate.runDir),
  })

  for (const candidate of candidates) {
    const check = checkStagedRun(root, candidate.runDir)
    if (!check.ok) {
      await log(root, client, "debug", "Analysis run candidate is not complete", {
        runDir: candidate.runDir,
        checkOutput: check.output,
      })
      continue
    }

    const pathInfo = writePathFile(candidate.runDir, candidate.solutionPath)
    deletePending(stateKey)
    await log(root, client, "info", "Wrote analysis solution path file", {
      ...pathInfo,
      sessionKey: stateKey,
      trigger,
    })
    return true
  }

  return false
}

async function handleCommandBefore(root, client, input) {
  const key = sessionKey(input)
  const runId = safePathSegment(key)
  pending.set(key, {
    startTime: Date.now(),
    existingRuns: listRunIds(root),
    runId,
  })

  await log(root, client, "debug", "Tracking test analysis workflow start", {
    sessionKey: key,
    runId,
    command: commandName(input),
    input: compactEvent(input),
  })
}

async function handleCommandExecuted(root, client, event) {
  const key = sessionKey(event)
  if (!pending.has(key)) {
    pending.set(key, {
      startTime: 0,
      existingRuns: new Set(),
      runId: safePathSegment(key),
    })
    await log(root, client, "warn", "Command completed without a matching before hook; using fallback scan", {
      sessionKey: key,
      event: compactEvent(event),
    })
  }

  const done = await scanState(root, client, key, "command.executed")
  if (!done && pending.has(key)) {
    deletePending(key)
    await log(root, client, "warn", "No completed analysis run found after command.executed", {
      sessionKey: key,
      event: compactEvent(event),
    })
  }
}

export const TestAnalysisOutputPathPlugin = async ({ client, directory, worktree }) => {
  const root = worktree || directory || process.cwd()
  await log(root, client, "info", "Plugin initialized", { root })

  return {
    "command.execute.before": async (input) => {
      try {
        await log(root, client, "debug", "Command before hook observed", {
          sessionKey: sessionKey(input),
          matched: isAnalysisCommand(input),
          input: compactEvent(input),
        })

        if (isAnalysisCommand(input)) {
          await handleCommandBefore(root, client, input)
        }
      } catch (error) {
        await log(root, client, "error", "Command before hook failed", {
          sessionKey: sessionKey(input),
          input: compactEvent(input),
          error: errorInfo(error),
        })
      }
    },
    "shell.env": async (input, output) => {
      try {
        const key = sessionKey(input)
        let state = pending.get(key)
        if (!state && pending.size === 1) {
          state = pending.values().next().value
        }
        if (!state?.runId || state.runId === "default") return

        output.env = output.env || {}
        output.env.TEST_ANALYSIS_RUN_ID = state.runId
        await log(root, client, "debug", "Injected test analysis run id into shell environment", {
          sessionKey: key,
          runId: state.runId,
          input: compactEvent(input),
        })
      } catch (error) {
        await log(root, client, "error", "Shell env hook failed", {
          sessionKey: sessionKey(input),
          input: compactEvent(input),
          error: errorInfo(error),
        })
      }
    },
    event: async ({ event }) => {
      try {
        if (event.type === "command.executed" || event.type === "tui.command.execute") {
          await log(root, client, "debug", "Command event observed", {
            type: event.type,
            sessionKey: sessionKey(event),
            matched: isAnalysisCommand(event),
            event: compactEvent(event),
          })
        }

        if (event.type === "command.executed" && isAnalysisCommand(event)) {
          await handleCommandExecuted(root, client, event)
          return
        }
      } catch (error) {
        await log(root, client, "error", "Event handler failed", {
          eventType: event?.type,
          sessionKey: sessionKey(event),
          event: compactEvent(event),
          error: errorInfo(error),
        })
      }
    },
  }
}
