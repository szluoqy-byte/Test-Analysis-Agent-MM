import { appendFileSync, existsSync, mkdirSync, readdirSync, statSync, writeFileSync } from "node:fs"
import { join, resolve } from "node:path"
import { spawnSync } from "node:child_process"

const COMMAND_NAME = "test-analysis-workflow"
const OUTPUT_FILE = "deliverables/test-analysis-solution.json"
const PATH_FILE = "path.txt"
const LOG_FILE = ".opencode/logs/test-analysis-output-path.log"
const MAX_IDLE_ATTEMPTS = 10
const MAX_RETRY_ATTEMPTS = 180
const RETRY_INTERVAL_MS = 10000
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

function isCommandEvent(event) {
  return event.type === "command.executed" || event.type === "tui.command.execute"
}

function isAnalysisCommand(event) {
  return JSON.stringify(event).includes(COMMAND_NAME)
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

function clearStateTimer(state) {
  if (state.timer) {
    clearTimeout(state.timer)
    state.timer = undefined
  }
}

function deletePending(stateKey) {
  const state = pending.get(stateKey)
  if (state) clearStateTimer(state)
  pending.delete(stateKey)
}

async function scanState(root, client, stateKey, trigger) {
  const state = pending.get(stateKey)
  if (!state) return false

  const candidates = findCandidateRuns(root, state)
  await log(root, client, "debug", "Candidate analysis runs scanned", {
    sessionKey: stateKey,
    trigger,
    retryAttempts: state.retryAttempts,
    idleAttempts: state.idleAttempts,
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

    const absoluteSolutionPath = resolve(candidate.solutionPath)
    const pathFile = join(candidate.runDir, PATH_FILE)
    mkdirSync(candidate.runDir, { recursive: true })
    writeFileSync(pathFile, `${absoluteSolutionPath}\n`, "utf8")
    deletePending(stateKey)
    await log(root, client, "info", "Wrote analysis solution path file", {
      pathFile,
      solutionPath: absoluteSolutionPath,
      trigger,
    })
    return true
  }

  return false
}

function scheduleRetry(root, client, stateKey) {
  const state = pending.get(stateKey)
  if (!state || state.timer) return

  state.timer = setTimeout(async () => {
    try {
      const current = pending.get(stateKey)
      if (!current) return
      current.timer = undefined
      current.retryAttempts += 1

      const done = await scanState(root, client, stateKey, "retry")
      if (done) return

      if (pending.has(stateKey) && current.retryAttempts >= MAX_RETRY_ATTEMPTS) {
        deletePending(stateKey)
        await log(root, client, "warn", "Stopped retrying completed analysis run lookup", {
          sessionKey: stateKey,
          retryAttempts: current.retryAttempts,
        })
        return
      }

      scheduleRetry(root, client, stateKey)
    } catch (error) {
      const current = pending.get(stateKey)
      if (current) {
        current.timer = undefined
        current.retryAttempts += 1
      }
      await log(root, client, "error", "Retry handler failed", {
        sessionKey: stateKey,
        retryAttempts: current?.retryAttempts,
        error: errorInfo(error),
      })
      if (pending.has(stateKey) && current?.retryAttempts < MAX_RETRY_ATTEMPTS) {
        scheduleRetry(root, client, stateKey)
      } else if (pending.has(stateKey)) {
        deletePending(stateKey)
        await log(root, client, "warn", "Stopped retrying after repeated hook errors", {
          sessionKey: stateKey,
          retryAttempts: current?.retryAttempts,
        })
      }
    }
  }, RETRY_INTERVAL_MS)
}

async function trackAnalysisCommand(root, client, event) {
  const key = sessionKey(event)
  pending.set(key, {
    startTime: Date.now(),
    existingRuns: listRunIds(root),
    idleAttempts: 0,
    retryAttempts: 0,
    timer: undefined,
  })

  await log(root, client, "debug", "Tracking test analysis workflow command", {
    sessionKey: key,
    eventType: event.type,
  })

  const done = await scanState(root, client, key, "command")
  if (!done) scheduleRetry(root, client, key)
}

async function handleIdle(root, client, event) {
  const key = sessionKey(event)
  const states = []
  if (pending.has(key)) {
    states.push([key, pending.get(key)])
  }

  await log(root, client, "debug", "Session idle observed", {
    sessionKey: key,
    pendingKeys: [...pending.keys()],
    matchedStates: states.map(([stateKey]) => stateKey),
  })

  for (const [stateKey, state] of states) {
    state.idleAttempts += 1
    await scanState(root, client, stateKey, "idle")

    if (pending.has(stateKey) && state.idleAttempts >= MAX_IDLE_ATTEMPTS) {
      await log(root, client, "debug", "Idle limit reached; retry timer remains authoritative", {
        sessionKey: stateKey,
        idleAttempts: state.idleAttempts,
      })
    }
  }
}

export const TestAnalysisOutputPathPlugin = async ({ client, directory, worktree }) => {
  const root = worktree || directory || process.cwd()
  await log(root, client, "info", "Plugin initialized", { root })

  return {
    event: async ({ event }) => {
      try {
        if (isCommandEvent(event)) {
          await log(root, client, "debug", "Command event observed", {
            type: event.type,
            sessionKey: sessionKey(event),
            matched: isAnalysisCommand(event),
            event: compactEvent(event),
          })
        }

        if (isCommandEvent(event) && isAnalysisCommand(event)) {
          await trackAnalysisCommand(root, client, event)
          return
        }

        if (event.type === "session.idle") {
          await handleIdle(root, client, event)
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
