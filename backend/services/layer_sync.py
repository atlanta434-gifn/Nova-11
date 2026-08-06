from models import Blueprint

def sync_layers(blueprint: Blueprint) -> Blueprint:
    # Mock logic to align layers based on room positions
    for layer in blueprint.layers:
        layer.elements = []
        for room in blueprint.rooms:
            layer.elements.append({
                "room": room.name,
                "position": room.position,
                "status": "aligned"
            })
    return blueprint

