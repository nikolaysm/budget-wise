import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // Lazy import to avoid bundling in edge
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const pkg = require('../../../package.json') as { version?: string }
    const version = typeof pkg.version === 'string' ? pkg.version : '0.0.0-dev'
    return NextResponse.json({ version })
  } catch {
    return NextResponse.json({ version: '0.0.0-dev' })
  }
}
