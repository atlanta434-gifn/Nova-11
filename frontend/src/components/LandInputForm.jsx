import { useState } from 'react'

export default function LandInputForm({ onGenerate }) {
  const [form, setForm] = useState({
    dimensions: { width: 10, length: 10, height: 3 },
    num_floors: 1,
    style: 'modern',
    budget_tier: 'mid'
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onGenerate(form)
  }

  const updateDim = (key, val) => {
    setForm(prev => ({
      ...prev,
      dimensions: { ...prev.dimensions, [key]: Number(val) }
    }))
  }

  return (
    <form onSubmit={handleSubmit} className="p-4 space-y-3">
      <h2 className="text-lg font-semibold mb-2">Land Input</h2>
      
      <div>
        <label className="block text-sm text-gray-300">Width (m)</label>
        <input 
          type="number" 
          step="0.1"
          value={form.dimensions.width} 
          onChange={e => updateDim('width', e.target.value)}
          className="w-full bg-white/10 border border-white/20 rounded px-2 py-1 focus:outline-none focus:border-blue-400"
        />
      </div>
      
      <div>
        <label className="block text-sm text-gray-300">Length (m)</label>
        <input 
          type="number" 
          step="0.1"
          value={form.dimensions.length} 
          onChange={e => updateDim('length', e.target.value)}
          className="w-full bg-white/10 border border-white/20 rounded px-2 py-1 focus:outline-none focus:border-blue-400"
        />
      </div>
      
      <div>
        <label className="block text-sm text-gray-300">Floors</label>
        <input 
          type="number" 
          min="1"
          value={form.num_floors} 
          onChange={e => setForm(prev => ({ ...prev, num_floors: Number(e.target.value) }))}
          className="w-full bg-white/10 border border-white/20 rounded px-2 py-1 focus:outline-none focus:border-blue-400"
        />
      </div>
      
      <div>
        <label className="block text-sm text-gray-300">Style</label>
        <select 
          value={form.style} 
          onChange={e => setForm(prev => ({ ...prev, style: e.target.value }))}
          className="w-full bg-white/10 border border-white/20 rounded px-2 py-1 focus:outline-none focus:border-blue-400"
        >
          <option value="modern">Modern</option>
          <option value="classic">Classic</option>
          <option value="minimalist">Minimalist</option>
        </select>
      </div>
      
      <div>
        <label className="block text-sm text-gray-300">Budget</label>
        <select 
          value={form.budget_tier} 
          onChange={e => setForm(prev => ({ ...prev, budget_tier: e.target.value }))}
          className="w-full bg-white/10 border border-white/20 rounded px-2 py-1 focus:outline-none focus:border-blue-400"
        >
          <option value="low">Low</option>
          <option value="mid">Mid</option>
          <option value="high">High</option>
        </select>
      </div>
      
      <button 
        type="submit" 
        className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-2 rounded transition"
      >
        Generate Blueprint
      </button>
    </form>
  )
}
