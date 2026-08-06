import uuid
from models import LandInput, Blueprint, Room, Layer, Dimensions

def generate_blueprint(input_data: LandInput) -> Blueprint:
    # Mock AI logic for blueprint generation
    rooms = []
    w, l = input_data.dimensions.width, input_data.dimensions.length
    
    # Simple layout: divide land into 4 quadrants
    rooms.append(Room(name="Living Room", position=[0, 0, 0], dimensions=Dimensions(width=w/2, length=l/2)))
    rooms.append(Room(name="Kitchen", position=[w/2, 0, 0], dimensions=Dimensions(width=w/2, length=l/2)))
    rooms.append(Room(name="Bedroom", position=[0, l/2, 0], dimensions=Dimensions(width=w/2, length=l/2)))
    rooms.append(Room(name="Bathroom", position=[w/2, l/2, 0], dimensions=Dimensions(width=w/2, length=l/2)))
    
    layers = [
        Layer(id=str(uuid.uuid4()), name="Electrical", type="electrical", elements=[]),
        Layer(id=str(uuid.uuid4()), name="Plumbing", type="plumbing", elements=[]),
        Layer(id=str(uuid.uuid4()), name="HVAC", type="hvac", elements=[]),
    ]
    
    return Blueprint(
        id=str(uuid.uuid4()),
        name=f"{input_data.style.title()} Smart Home",
        rooms=rooms,
        layers=layers,
        metadata={"input": input_data.dict()}
    )

