import { appendFileSync, existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs"
import { join, resolve } from "node:path"
import { spawnSync } from "node:child_process"

const OUTPUT_FILE = "deliverables/test-analysis-solution.json"
const PATH_FILE = "path.txt"
const LOG_FILE = ".opencode/logs/test-analysis-output-path.log"
const RUN_ID_ENV_VAR = "TEST_ANALYSIS_RUN_ID"
const RUN_ID_RE = /^[A-Za-z0-9._-]+$/

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

function sessionKey(value) {
  return findStringValue(value, ["sessionID", "sessionId", "session"])
}

function runIdForSession(value) {
  const key = sessionKey(value)
  if (!key || !RUN_ID_RE.test(key)) return undefined
  return key
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
    error: result.error ? errorInfo(result.error) : undefined,
  }
}

async function log(root, client, level, message, extra = {}) {
  try {
    writeLocalLog(root, level, message, extra)
  } catch {
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

function writePathFile(runDir, solutionPath) {
  const absoluteSolutionPath = resolve(solutionPath)
  const runPathFile = join(runDir, PATH_FILE)
  writeFileSync(runPathFile, `${absoluteSolutionPath}\n`, "utf8")

  return {
    pathFile: runPathFile,
    solutionPath: absoluteSolutionPath,
  }
}

function isCurrentPathFile(runDir, solutionPath) {
  const runPathFile = join(runDir, PATH_FILE)
  if (!existsSync(runPathFile)) return false

  try {
    const recordedPath = readFileSync(runPathFile, "utf8").trim()
    if (recordedPath !== resolve(solutionPath)) return false
    return statSync(runPathFile).mtimeMs >= statSync(solutionPath).mtimeMs
  } catch {
    return false
  }
}

async function finalizeAnalysisRun(root, client, value, trigger) {
  const sessionID = sessionKey(value)
  const runId = runIdForSession(value)
  if (!runId) {
    await log(root, client, "warn", "Ignored session event with invalid session id", {
      sessionID,
      trigger,
      event: compactEvent(value),
    })
    return false
  }

  const runDir = join(root, "outputs", "runs", runId)
  const solutionPath = join(runDir, OUTPUT_FILE)
  if (!existsSync(solutionPath)) {
    await log(root, client, "debug", "Session has no test analysis solution", {
      sessionID,
      runDir,
      trigger,
    })
    return false
  }

  if (isCurrentPathFile(runDir, solutionPath)) {
    await log(root, client, "debug", "Analysis solution path file is already current", {
      sessionID,
      runDir,
      trigger,
    })
    return true
  }

  const check = checkStagedRun(root, runDir)
  if (!check.ok) {
    await log(root, client, "warn", "Analysis run is not complete at session idle", {
      sessionID,
      runDir,
      trigger,
      checkOutput: check.output,
      checkError: check.error,
    })
    return false
  }

  const pathInfo = writePathFile(runDir, solutionPath)
  await log(root, client, "info", "Wrote analysis solution path file", {
    ...pathInfo,
    sessionID,
    trigger,
  })
  return true
}

export const TestAnalysisOutputPathPlugin = async ({ client, directory, worktree }) => {
  const root = worktree || directory || process.cwd()
  await log(root, client, "info", "Plugin initialized", { root })

  return {
    "shell.env": async (input, output) => {
      try {
        const runId = runIdForSession(input)
        if (!runId) {
          await log(root, client, "warn", "Skipped run id injection for invalid session id", {
            sessionID: sessionKey(input),
            input: compactEvent(input),
          })
          return
        }

        output.env = output.env || {}
        output.env[RUN_ID_ENV_VAR] = runId
        await log(root, client, "debug", "Injected test analysis run id into shell environment", {
          sessionID: runId,
          runId,
        })
      } catch (error) {
        await log(root, client, "error", "Shell env hook failed", {
          sessionID: sessionKey(input),
          input: compactEvent(input),
          error: errorInfo(error),
        })
      }
    },
    event: async ({ event }) => {
      try {
        if (event.type !== "session.idle") return

        await log(root, client, "debug", "Session idle observed", {
          sessionID: sessionKey(event),
          event: compactEvent(event),
        })
        await finalizeAnalysisRun(root, client, event, "session.idle")
      } catch (error) {
        await log(root, client, "error", "Event handler failed", {
          eventType: event?.type,
          sessionID: sessionKey(event),
          event: compactEvent(event),
          error: errorInfo(error),
        })
      }
    },
  }
}
