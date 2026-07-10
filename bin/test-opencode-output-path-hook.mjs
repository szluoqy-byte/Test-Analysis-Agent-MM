#!/usr/bin/env node

import assert from "node:assert/strict"
import { spawnSync } from "node:child_process"
import { cpSync, existsSync, mkdirSync, readFileSync, rmSync, statSync } from "node:fs"
import { dirname, join, resolve } from "node:path"
import { fileURLToPath, pathToFileURL } from "node:url"

const scriptDir = dirname(fileURLToPath(import.meta.url))
const root = resolve(scriptDir, "..")
const pluginPath = join(root, ".opencode", "plugins", "test-analysis-output-path.js")
const fixtureDir = join(root, "examples", "outputs", "runs", "sample-requirement-run")
const sessionID = `ses_hook_test_${process.pid}_${Date.now()}`
const unrelatedSessionID = `${sessionID}_unrelated`
const incompleteSessionID = `${sessionID}_incomplete`
const runDir = join(root, "outputs", "runs", sessionID)
const unrelatedRunDir = join(root, "outputs", "runs", unrelatedSessionID)
const incompleteRunDir = join(root, "outputs", "runs", incompleteSessionID)
const solutionPath = join(runDir, "deliverables", "test-analysis-solution.json")
const pathFile = join(runDir, "path.txt")
const logs = []

const client = {
  app: {
    async log(entry) {
      logs.push(entry.body)
    },
  },
}

try {
  assert.equal(existsSync(pluginPath), true, `missing plugin: ${pluginPath}`)
  assert.equal(existsSync(fixtureDir), true, `missing fixture: ${fixtureDir}`)
  assert.equal(existsSync(runDir), false, `test run already exists: ${runDir}`)

  const moduleUrl = `${pathToFileURL(pluginPath).href}?test=${Date.now()}`
  const { TestAnalysisOutputPathPlugin } = await import(moduleUrl)
  const hooks = await TestAnalysisOutputPathPlugin({ client, directory: root, worktree: root })

  const envOutput = { env: {} }
  await hooks["shell.env"]({ sessionID, cwd: root, callID: "call-test" }, envOutput)
  assert.equal(envOutput.env.TEST_ANALYSIS_RUN_ID, sessionID)
  const generatedRunId = spawnSync("python", ["bin/generate-run-id.py"], {
    cwd: root,
    encoding: "utf8",
    env: { ...process.env, ...envOutput.env },
    windowsHide: true,
  })
  assert.equal(generatedRunId.status, 0, generatedRunId.stderr)
  assert.equal(generatedRunId.stdout.trim(), sessionID)

  cpSync(fixtureDir, runDir, { recursive: true })
  await hooks.event({ event: { type: "session.idle", properties: { sessionID } } })

  assert.equal(existsSync(pathFile), true, "session.idle did not create path.txt")
  assert.equal(readFileSync(pathFile, "utf8").trim(), resolve(solutionPath))
  assert.equal(
    logs.some((entry) => entry.level === "info" && entry.message === "Wrote analysis solution path file"),
    true,
    "success log was not emitted",
  )

  const firstPathFileMtime = statSync(pathFile).mtimeMs
  await hooks.event({ event: { type: "session.idle", properties: { sessionID } } })
  assert.equal(statSync(pathFile).mtimeMs, firstPathFileMtime, "duplicate idle rewrote a current path.txt")
  assert.equal(
    logs.filter((entry) => entry.level === "info" && entry.message === "Wrote analysis solution path file").length,
    1,
    "duplicate idle emitted another path write",
  )

  mkdirSync(join(incompleteRunDir, "deliverables"), { recursive: true })
  cpSync(
    join(fixtureDir, "deliverables", "test-analysis-solution.json"),
    join(incompleteRunDir, "deliverables", "test-analysis-solution.json"),
  )
  await hooks.event({
    event: { type: "session.idle", properties: { sessionID: incompleteSessionID } },
  })
  assert.equal(
    existsSync(join(incompleteRunDir, "path.txt")),
    false,
    "incomplete staged run created path.txt",
  )

  await hooks.event({
    event: { type: "session.idle", properties: { sessionID: unrelatedSessionID } },
  })
  assert.equal(existsSync(unrelatedRunDir), false, "unrelated idle created a run directory")

  console.log("OpenCode output path hook test passed")
} finally {
  rmSync(runDir, { recursive: true, force: true })
  rmSync(unrelatedRunDir, { recursive: true, force: true })
  rmSync(incompleteRunDir, { recursive: true, force: true })
}
