import json
import random


def generate_blocks(num_blocks):
    blocks = []
    ecp_generated = False

    for _ in range(num_blocks):
        x = random.randint(1, 16)
        y = random.randint(1, 4)

        # Check if the current block is the one before the ecp object
        if not ecp_generated and random.random() < 0.1:
            blocks.append({
                "x": x,
                "y": y,
                "width": 96,
                "height": 96,
                "left": 192,
                "top": 64
            })
            ecp_generated = True
        else:
            blocks.append({
                "x": x,
                "y": y,
                "width": 96,
                "height": 96,
                "left": 192,
                "top": 64
            })

    return blocks


def generate_fires(blocks):
    fire_objects = []

    for block in random.sample(blocks, min(len(blocks), 3)):
        fire_objects.append({
            "width": 16,
            "height": 32,
            "x": block["x"] + 0.5,
            "y": block["y"]
        })

    return fire_objects


def generate_map(map_name):
    num_blocks = 10
    blocks = generate_blocks(num_blocks)
    fires = generate_fires(blocks)

    # Find the block with the highest x for ecp placement
    ecp_block = max(blocks, key=lambda block: block["x"])
    ecp = {
        "width": 64,
        "height": 64,
        "x": ecp_block["x"] - 0.5,
        "y": ecp_block["y"] + 0.5
    }

    data = {
        "map_name": map_name,
        "floorX": 96,
        "floorY": 64,
        "background": "Yellow",
        "blocks": blocks,
        "fires": fires,
        "ecp": [ecp]
    }

    return data


def save_to_json(data, filename):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=2)


if __name__ == "__main__":
    for i in range(5,8):  # Generate 5 maps
        map_data = generate_map(f"Map_{i + 1}")
        save_to_json(map_data, f"map_{i + 1}.json")
