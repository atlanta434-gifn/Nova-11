import { Zap, Droplets, Wind, RefreshCw } from 'lucide-react'

const layerIcons = {
  electrical: Zap,
  plumbing: Droplets,
  hvac: Wind,
}

export default function LayerPanel({ layers, activeLayers, onToggle, onSync }) {
  if (!layers?.length) return null

  return (
    <div className="p-4 border-t border-white/10">
      <h3 className="text-md font-semibold mb-2">Layers</h3>
      <div className="space-y-2 mb-4">
        {layers.map(layer => {
          const Icon = layerIcons[layer.type] || Zap
          const isActive = activeLayers.includes(layer.id)
          return (
            <button
              key={layer.id}
              onClick={() => onToggle(layer.id)}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded transition border ${
                isActive 
                  ? 'bg-blue-500/20 border-blue-400/40 text-blue-200' 
                  : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span className="text-sm">{layer.name}</span>
            </button>
          )
        })}
      </div>
      <button
        onClick={onSync}
        className="w-full flex items-center justify-center gap-2 bg-emerald-600/80 hover:bg-emerald-500/80 text-white py-2 rounded transition"
      >
        <RefreshCw className="w-4 h-4" />
        Sync Layers
      </button>
    </div>
  )
}
