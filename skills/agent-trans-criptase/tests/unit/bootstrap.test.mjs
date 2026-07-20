import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { ensureSkillLink, hasTransRegistration, probeMcpServer } from '../../scripts/bootstrap.mjs'

test('detects both CLI and config-file forms of a trans registration', () => {
    assert.equal(hasTransRegistration('trans: node /tmp/server.mjs'), true)
    assert.equal(hasTransRegistration('[mcp_servers.trans]'), true)
    assert.equal(hasTransRegistration('no servers registered'), false)
})

test('creates an idempotent skill link without replacing a non-link path', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'trans-bootstrap-'))
    const source = path.join(root, 'source')
    const target = path.join(root, 'target')
    fs.mkdirSync(source)

    assert.equal(ensureSkillLink(target, source).status, 'PASS')
    assert.equal(ensureSkillLink(target, source).detail, 'already linked')

    const occupied = path.join(root, 'occupied')
    fs.mkdirSync(occupied)
    assert.equal(ensureSkillLink(occupied, source).status, 'WARN')
    fs.rmSync(root, { recursive: true, force: true })
})

test('starts the bundled MCP server and completes initialize', async () => {
    const result = await probeMcpServer()
    assert.equal(result.status, 'PASS', result.detail)
})
