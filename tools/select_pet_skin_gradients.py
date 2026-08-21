"""Select deterministic real pet skins from Core Keeper's PetInfosTable."""

import argparse
import json
from pathlib import Path


CHECK_TO_PET = {
    "hatch_subterrier": "PetDog", "hatch_embertail": "PetCat",
    "hatch_owlux": "PetBird", "hatch_jr_orange_slime": "PetSlimeBlob",
    "hatch_earie": "PetWarlock", "hatch_prince_slime": "PetPrinceSlimeBlob",
    "hatch_fanhare": "PetBunny", "hatch_jr_purple_slime": "PetPoisonSlimeBlob",
    "hatch_pheromoth": "PetMoth", "hatch_jr_blue_slime": "PetSlipperySlimeBlob",
    "hatch_jr_lava_slime": "PetLavaSlimeBlob", "hatch_snugglygrade": "PetTardigrade",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("export", type=Path)
    args = parser.parse_args()
    path = args.export / "pet-skins/manifest.json"
    data = json.loads(path.read_text())
    table = next(row for row in data if row.get("$type") == "PetInfosTable")
    skins = {row["petId"]: row for row in table["petSkins"]}
    output = {}
    for check, pet_id in CHECK_TO_PET.items():
        # Skin zero is a real selectable skin and keeps local builds deterministic.
        block = skins[pet_id]["skins"][0]["gradientMapRef"]["reference"]["m_cachedDataBlock"]
        output[check] = {
            "pet_id": pet_id,
            "skin_index": 0,
            "palette": [[int(c[k]) for k in ("r", "g", "b")] for c in block["array"]],
            "source": f"PetInfosTable/{pet_id}/skins/0/gradientMapRef",
        }
    selected = args.export / "pet-skins/selected-gradients.json"
    # PetElectric and PetMagic use already-colored fixed ObjectInfo icons. They
    # must not receive a selectable-pet gradient or an inferred second tint.
    selected.write_text(json.dumps(output, indent=2) + "\n")
    print(f"Selected {len(output)} deterministic pet gradients ({len(CHECK_TO_PET)} direct skin references).")


if __name__ == "__main__":
    main()
