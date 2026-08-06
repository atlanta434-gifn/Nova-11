import { useState } from 'react'
import { useBlueprint } from '../hooks/useBlueprint'
import LandInputForm from './LandInputForm'
import BlueprintViewer from './BlueprintViewer'
import LayerPanel from './LayerPanel'
import LayoutSelector from './LayoutSelector'
import AILoadingOverlay from './AILoadingOverlay'

export default function Dashboard() {
  const { blueprint, loading, error, generateBlueprint, syncLayers } = useBlueprint()
  const [activeLayers, setActiveLayers] = useState([])
  const [selectedRoom, setSelectedRoom] = useState(null)

  const handleGenerate = async (data) => {
    await generateBlueprint(data)
  }

  const toggleLayer = (layerId) => {
    setActiveLayers(prev => 
      prev.includes(layerId) ? prev.filter(id => id !== layerId) : [...prev, layerId]
    )
  }

  const handleSync = async () => {
    if (blueprint) {
      await syncLayers(blueprint)
    }
  }

  return (
    <div className="h-screen flex flex-col">
      <header className="p-4 glass border-b border-white/10">
        <h1 className="text-2xl font-bold">Smart Home AI Blueprint</h1>
      </header>
      
      <main className="flex-1 flex overflow-hidden">
        <aside className="w-80 glass border-r border-white/10 flex flex-col overflow-y-auto">
          <LandInputForm onGenerate={handleGenerate} />
          {blueprint && (
            <>
              <LayoutSelector 
                rooms={blueprint.rooms} 
                selected={selectedRoom} 
                onSelect={setSelectedRoom} 
              />
              <LayerPanel 
                layers={blueprint.layers} 
                activeLayers={activeLayers} 
                onToggle={toggleLayer}
                onSync={handleSync}
              />
            </>
          )}
        </aside>
        
        <section className="flex-1 relative bg-slate-950">
          <BlueprintViewer 
            blueprint={blueprint} 
            activeLayers={activeLayers}
            selectedRoom={selectedRoom}
          />
          {loading && <AILoadingOverlay />}
        </section>
      </main>
      
      {error && (
        <div className="absolute bottom-4 right-4 bg-red-500/90 text-white px-4 py-2 rounded shadow-lg z-50">
          {error}
        </div>
      )}
    </div>
  )
}
