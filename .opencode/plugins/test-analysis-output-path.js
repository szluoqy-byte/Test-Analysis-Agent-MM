import { existsSync, readFileSync, statSync, writeFileSync } from "node:fs"
import { join, resolve } from "node:path"

const OUTPUT_ARTIFACTS = [
  {
    kind: "analysis",
    solutionFile: "deliverables/test-analysis-solution.json",
    pathFile: "path_analysis.txt",
  },
  {
    kind: "design",
    solutionFile: "deliverables/test-design-solution.json",
    pathFile: "path_design.txt",
  },
]
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

async function log(client, level, message, extra = {}) {
  if (!client?.app?.log) return
  try {
    await client.app.log({
      body: {
        service: "test-solution-output-path",
        level,
        message,
        extra,
      },
    })
  } catch {
    // Logging failures must not interrupt the session hook.
  }
}

function writePathFile(runDir, solutionPath, pathFile) {
  const absoluteSolutionPath = resolve(solutionPath)
  const runPathFile = join(runDir, pathFile)
  writeFileSync(runPathFile, `${absoluteSolutionPath}\n`, "utf8")

  return {
    pathFile: runPathFile,
    solutionPath: absoluteSolutionPath,
  }
}

function isCurrentPathFile(runDir, solutionPath, pathFile) {
  const runPathFile = join(runDir, pathFile)
  if (!existsSync(runPathFile)) return false

  try {
    const recordedPath = readFileSync(runPathFile, "utf8").trim()
    if (recordedPath !== resolve(solutionPath)) return false
    return statSync(runPathFile).mtimeMs >= statSync(solutionPath).mtimeMs
  } catch {
    return false
  }
}

async function publishArtifactPath(root, client, runDir, sessionID, artifact, trigger) {
  const solutionPath = join(runDir, artifact.solutionFile)
  if (!existsSync(solutionPath)) {
    await log(client, "debug", `Session has no ${artifact.kind} solution`, {
      sessionID,
      runDir,
      trigger,
      solutionPath,
    })
    return false
  }

  if (isCurrentPathFile(runDir, solutionPath, artifact.pathFile)) {
    await log(client, "debug", `${artifact.kind} solution path file is already current`, {
      sessionID,
      runDir,
      trigger,
      pathFile: artifact.pathFile,
    })
    return true
  }

  const pathInfo = writePathFile(runDir, solutionPath, artifact.pathFile)
  await log(client, "info", `Wrote ${artifact.kind} solution path file`, {
    ...pathInfo,
    sessionID,
    trigger,
    kind: artifact.kind,
  })
  return true
}

async function publishSessionArtifactPaths(root, client, value, trigger) {
  const sessionID = sessionKey(value)
  const runId = runIdForSession(value)
  if (!runId) {
    await log(client, "warn", "Ignored session event with invalid session id", {
      sessionID,
      trigger,
      event: compactEvent(value),
    })
    return false
  }

  const runDir = join(root, "outputs", "runs", runId)
  let published = false
  for (const artifact of OUTPUT_ARTIFACTS) {
    published = (await publishArtifactPath(root, client, runDir, sessionID, artifact, trigger)) || published
  }
  return published
}

export const TestAnalysisOutputPathPlugin = async ({ client, directory, worktree }) => {
  const root = worktree || directory || process.cwd()
  await log(client, "info", "Plugin initialized", { root })

  return {
    "shell.env": async (input, output) => {
      try {
        const runId = runIdForSession(input)
        if (!runId) {
          await log(client, "warn", "Skipped run id injection for invalid session id", {
            sessionID: sessionKey(input),
            input: compactEvent(input),
          })
          return
        }

        output.env = output.env || {}
        output.env[RUN_ID_ENV_VAR] = runId
        await log(client, "debug", "Injected test analysis run id into shell environment", {
          sessionID: runId,
          runId,
        })
      } catch (error) {
        await log(client, "error", "Shell env hook failed", {
          sessionID: sessionKey(input),
          input: compactEvent(input),
          error: errorInfo(error),
        })
      }
    },
    event: async ({ event }) => {
      try {
        if (event.type !== "session.idle") return

        await log(client, "debug", "Session idle observed", {
          sessionID: sessionKey(event),
          event: compactEvent(event),
        })
        await publishSessionArtifactPaths(root, client, event, "session.idle")
      } catch (error) {
        await log(client, "error", "Event handler failed", {
          eventType: event?.type,
          sessionID: sessionKey(event),
          event: compactEvent(event),
          error: errorInfo(error),
        })
      }
    },
  }
}
