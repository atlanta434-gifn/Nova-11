import { useMemo } from 'react'
import * as THREE from 'three'

function RoomBox({ room, isSelected }) {
  const { position, dimensions } = room
  const [x, y, z] = position
  const w = dimensions.width
  const h = dimensions.height || 3
  const l = dimensions.length

  const edgesGeometry = useMemo(() => {
    const geo = new THREE.BoxGeometry(w, h, l)
    return new THREE.EdgesGeometry(geo)
  }, [w, h, l])

  return (
    <group position={[x + w / 2, h / 2, z + l / 2]}>
      <mesh>
        <boxGeometry args={[w, h, l]} />
        <meshStandardMaterial 
          color={isSelected ? '#3b82f6' : '#64748b'} 
          transparent 
          opacity={0.6} 
        />
      </mesh>
      <lineSegments geometry={edgesGeometry}>
        <lineBasicMaterial color={isSelected ? '#60a5fa' : '#94a3b8'} />
      </lineSegments>
    </group>
  )
}

export default function ThreeScene({ blueprint, activeLayers, selectedRoom }) {
  const rooms = blueprint?.rooms || []
  
  return (
    <group>
      {rooms.map((room, i) => (
        <RoomBox 
          key={i} 
          room={room} 
          isSelected={selectedRoom?.name === room.name} 
        />
      ))}
      
      {blueprint?.layers?.map(layer => {
        if (!activeLayers.includes(layer.id)) return null
        return layer.elements?.map((el, i) => {
          const [x, y, z] = el.position
          const color = 
            layer.type === 'electrical' ? '#fbbf24' : 
            layer.type === 'plumbing' ? '#38bdf8' : '#a78bfa'
          return (
            <mesh key={`${layer.id}-${i}`} position={[x + 0.5, 0.3, z + 0.5]}>
              <sphereGeometry args={[0.3, 16, 16]} />
              <meshStandardMaterial 
                color={color} 
                emissive={color}
                emissiveIntensity={0.5}
              />
            </mesh>
          )
        })
      })}
    </group>
  )
}
