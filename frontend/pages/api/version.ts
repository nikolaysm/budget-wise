import type { NextApiRequest, NextApiResponse } from 'next'

// Lazy load to avoid bundling package.json into client
export default function handler(_req: NextApiRequest, res: NextApiResponse) {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const pkg = require('../../package.json') as { version?: string }
    const version = typeof pkg.version === 'string' ? pkg.version : '0.0.0-dev'
    res.status(200).json({ version })
  } catch (e) {
    res.status(200).json({ version: '0.0.0-dev' })
  }
}
