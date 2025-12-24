import { Agent } from '@strands-agents/sdk'
import express, { type Request, type Response } from 'express'

const PORT = Number(process.env.PORT) || 8080

// Configure the agent with default Bedrock model
const agent = new Agent()

const app = express()

// Middleware to parse JSON
app.use(express.json())

// Health check endpoint (REQUIRED)
app.get('/ping', (_, res) =>
  res.json({
    status: 'healthy',
  })
)

// Agent invocation endpoint (REQUIRED)
app.post('/invocations', async (req: Request, res: Response) => {
  try {
    const { input } = req.body
    const prompt = input?.prompt || ''
    
    if (!prompt) {
      return res.status(400).json({
        detail: 'No prompt found in input. Please provide a "prompt" key in the input.'
      })
    }

    // Invoke the agent
    const result = await agent.invoke(prompt)
    
    const response = {
      message: result,
      timestamp: new Date().toISOString(),
      model: 'strands-agent',
    }

    return res.json({ output: response })
  } catch (err) {
    console.error('Error processing request:', err)
    return res.status(500).json({ 
      detail: `Agent processing failed: ${err instanceof Error ? err.message : 'Unknown error'}` 
    })
  }
})

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Strands Agent Server listening on port ${PORT}`)
  console.log(`📍 Endpoints:`)
  console.log(`   POST http://0.0.0.0:${PORT}/invocations`)
  console.log(`   GET  http://0.0.0.0:${PORT}/ping`)
})
