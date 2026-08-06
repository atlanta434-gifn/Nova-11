export default function LayoutSelector({ rooms, selected, onSelect }) {
  if (!rooms?.length) return null

  return (
    <div className="p-4 border-t border-white/10">
      <h3 className="text-md font-semibold mb-2">Rooms</h3>
      <div className="space-y-1">
        {rooms.map((room, i) => (
          <button
            key={i}
            onClick={() => onSelect(room)}
            className={`w-full text-left px-3 py-2 rounded transition ${
              selected?.name === room.name 
                ? 'bg-blue-500/30 border border-blue-400/50' 
                : 'hover:bg-white/5 border border-transparent'
            }`}
          >
            <div className="font-medium text-sm">{room.name}</div>
            <div className="text-xs text-gray-400">
              {room.dimensions.width.toFixed(1)}m × {room.dimensions.length.toFixed(1)}m
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
