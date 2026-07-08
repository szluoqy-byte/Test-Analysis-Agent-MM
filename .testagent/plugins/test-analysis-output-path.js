import { existsSync, mkdirSync, readdirSync, statSync, writeFileSync } from "node:fs"
import { join, resolve } from "node:path"
import { spawnSync } from "node:child_process"

const COMMAND_NAME = "test-analysis-workflow"
const OUTPUT_FILE = "deliverables/test-analysis-solution.json"
const PATH_FILE = "path.txt"
const MAX_IDLE_ATTEMPTS = 10
const START_TIME_SKEW_MS = 5000

const pending = new Map()

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

async function log(client, level, message, extra = {}) {
  if (!client?.app?.log) return
  await client.app.log({
    body: {
      service: "test-analysis-output-path",
      level,
      message,
      extra,
    },
  })
}

async function handleIdle(root, client, event) {
  const key = sessionKey(event)
  const states = []
  if (pending.has(key)) {
    states.push([key, pending.get(key)])
  } else if (pending.has("default")) {
    states.push(["default", pending.get("default")])
  } else if (key === "default") {
    states.push(...pending.entries())
  }

  for (const [stateKey, state] of states) {
    state.idleAttempts += 1
    const candidates = findCandidateRuns(root, state)
    for (const candidate of candidates) {
      const check = checkStagedRun(root, candidate.runDir)
      if (!check.ok) {
        await log(client, "debug", "Analysis run candidate is not complete", {
          runDir: candidate.runDir,
          checkOutput: check.output,
        })
        continue
      }

      const absoluteSolutionPath = resolve(candidate.solutionPath)
      const pathFile = join(candidate.runDir, PATH_FILE)
      mkdirSync(candidate.runDir, { recursive: true })
      writeFileSync(pathFile, `${absoluteSolutionPath}\n`, "utf8")
      pending.delete(stateKey)
      await log(client, "info", "Wrote analysis solution path file", {
        pathFile,
        solutionPath: absoluteSolutionPath,
      })
      break
    }

    if (pending.has(stateKey) && state.idleAttempts >= MAX_IDLE_ATTEMPTS) {
      pending.delete(stateKey)
      await log(client, "warn", "Stopped waiting for completed analysis run", {
        sessionKey: stateKey,
        idleAttempts: state.idleAttempts,
      })
    }
  }
}

export const TestAnalysisOutputPathPlugin = async ({ client, directory, worktree }) => {
  const root = worktree || directory || process.cwd()

  return {
    event: async ({ event }) => {
      if (event.type === "command.executed" && isAnalysisCommand(event)) {
        pending.set(sessionKey(event), {
          startTime: Date.now(),
          existingRuns: listRunIds(root),
          idleAttempts: 0,
        })
        await log(client, "debug", "Tracking test analysis workflow command", {
          sessionKey: sessionKey(event),
        })
        return
      }

      if (event.type === "session.idle") {
        await handleIdle(root, client, event)
      }
    },
  }
}
