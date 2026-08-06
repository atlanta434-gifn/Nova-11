import { useState } from 'react'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

export function useBlueprint() {
  const [blueprint, setBlueprint] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const generateBlueprint = async (inputData) => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.post(`${API_URL}/generate`, inputData)
      setBlueprint(res.data)
      return res.data
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const syncLayers = async (bp) => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.post(`${API_URL}/sync-layers`, bp)
      setBlueprint(res.data)
      return res.data
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  return { blueprint, loading, error, generateBlueprint, syncLayers }
}
