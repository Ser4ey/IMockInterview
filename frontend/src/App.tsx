import { useState } from 'react'
import { Button, Container, Typography, Box } from '@mui/material'

function App() {
  const [count, setCount] = useState(0)

  return (
    <Container maxWidth="sm">
      <Box sx={{ my: 4, textAlign: 'center' }}>
        <Typography variant="h2" component="h1" gutterBottom>
          IMock
        </Typography>
        <Typography variant="h5" component="h2" gutterBottom>
          AI Interview Platform
        </Typography>
        <Box sx={{ mt: 4 }}>
          <Button variant="contained" onClick={() => setCount((count) => count + 1)}>
            count is {count}
          </Button>
        </Box>
      </Box>
    </Container>
  )
}

export default App
