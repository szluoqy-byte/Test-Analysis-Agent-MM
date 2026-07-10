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
const analysisOnlySessionID = `${sessionID}_analysis_only`
const designOnlySessionID = `${sessionID}_design_only`
const unrelatedSessionID = `${sessionID}_unrelated`
const runDir = join(root, "outputs", "runs", sessionID)
const analysisOnlyRunDir = join(root, "outputs", "runs", analysisOnlySessionID)
const designOnlyRunDir = join(root, "outputs", "runs", designOnlySessionID)
const unrelatedRunDir = join(root, "outputs", "runs", unrelatedSessionID)
const analysisSolutionPath = join(runDir, "deliverables", "test-analysis-solution.json")
const designSolutionPath = join(runDir, "deliverables", "test-design-solution.json")
const analysisPathFile = join(runDir, "path_analysis.txt")
const designPathFile = join(runDir, "path_design.txt")
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
  assert.equal(logs.every((entry) => entry.service === "test-solution-output-path"), true)

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

  assert.equal(existsSync(analysisPathFile), true, "session.idle did not create path_analysis.txt")
  assert.equal(existsSync(designPathFile), true, "session.idle did not create path_design.txt")
  assert.equal(readFileSync(analysisPathFile, "utf8").trim(), resolve(analysisSolutionPath))
  assert.equal(readFileSync(designPathFile, "utf8").trim(), resolve(designSolutionPath))
  assert.equal(existsSync(join(runDir, "path.txt")), false, "legacy path.txt was created")
  assert.equal(logs.every((entry) => entry.service === "test-solution-output-path"), true)

  const firstAnalysisMtime = statSync(analysisPathFile).mtimeMs
  const firstDesignMtime = statSync(designPathFile).mtimeMs
  await hooks.event({ event: { type: "session.idle", properties: { sessionID } } })
  assert.equal(statSync(analysisPathFile).mtimeMs, firstAnalysisMtime)
  assert.equal(statSync(designPathFile).mtimeMs, firstDesignMtime)
  assert.equal(
    logs.filter((entry) => entry.level === "info" && entry.message.startsWith("Wrote ")).length,
    2,
    "duplicate idle emitted another path write",
  )

  mkdirSync(join(analysisOnlyRunDir, "deliverables"), { recursive: true })
  cpSync(
    join(fixtureDir, "deliverables", "test-analysis-solution.json"),
    join(analysisOnlyRunDir, "deliverables", "test-analysis-solution.json"),
  )
  await hooks.event({
    event: { type: "session.idle", properties: { sessionID: analysisOnlySessionID } },
  })
  assert.equal(existsSync(join(analysisOnlyRunDir, "path_analysis.txt")), true)
  assert.equal(existsSync(join(analysisOnlyRunDir, "path_design.txt")), false)

  mkdirSync(join(designOnlyRunDir, "deliverables"), { recursive: true })
  cpSync(
    join(fixtureDir, "deliverables", "test-design-solution.json"),
    join(designOnlyRunDir, "deliverables", "test-design-solution.json"),
  )
  await hooks.event({
    event: { type: "session.idle", properties: { sessionID: designOnlySessionID } },
  })
  assert.equal(existsSync(join(designOnlyRunDir, "path_analysis.txt")), false)
  assert.equal(existsSync(join(designOnlyRunDir, "path_design.txt")), true)

  await hooks.event({
    event: { type: "session.idle", properties: { sessionID: unrelatedSessionID } },
  })
  assert.equal(existsSync(unrelatedRunDir), false, "unrelated idle created a run directory")

  console.log("OpenCode output path hook test passed")
} finally {
  rmSync(runDir, { recursive: true, force: true })
  rmSync(analysisOnlyRunDir, { recursive: true, force: true })
  rmSync(designOnlyRunDir, { recursive: true, force: true })
  rmSync(unrelatedRunDir, { recursive: true, force: true })
}
