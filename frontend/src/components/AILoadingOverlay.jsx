import { Loader2 } from 'lucide-react'

export default function AILoadingOverlay() {
  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="glass p-8 rounded-2xl flex flex-col items-center gap-4">
        <Loader2 className="w-10 h-10 animate-spin text-blue-400" />
        <p className="text-lg font-medium text-blue-100">AI Generating Blueprint...</p>
      </div>
    </div>
  )
}
