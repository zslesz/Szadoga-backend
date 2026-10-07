from app.schemas.schema import Item, Container
from app.services.packer import BinPacker3D
from app.services.solver import WeightAndBalanceEngine

def run_contour_test():
    uld_container = Container(
        id="ULD-AKE-CONTOUR",
        name="Contoured LD3 Container",
        width=200.7,
        height=162.6,
        depth=153.4,
        max_weight=1588.0,
        base_width=156.2,
        contour_height=45.0,
        cog_target_x=100.35,
        cog_target_y=76.7,
        cog_target_z=81.3
    )


    import random
    items = []
    for i in range(1, 71):
        items.append(
            Item(
                id=f"BOX-{i}",
                width=random.choice([30.0, 40.0, 50.0]),
                height=random.choice([30.0, 40.0, 50.0]),
                depth=random.choice([30.0, 40.0, 50.0]),
                weight=round(random.uniform(10.0, 50.0), 1),
                can_rotate = True
            )
        )

    packer = BinPacker3D(uld_container)
    placed, unpacked = packer.pack(items)

    valid, cog_metrics = WeightAndBalanceEngine.is_cog_valid(uld_container, placed)

    total_volume = sum(p.item.volume for p in placed)
    utilization = round((total_volume / uld_container.max_volume) * 100, 2)

    print("=== FERDE KONTÚROS (CONTOUR) PAKOLÁSI TESZT ===")
    print(f"Konténer alsó szélessége (base_width): {uld_container.base_width} cm")
    print(f"Dőlés magassága (contour_height): {uld_container.contour_height} cm")
    print(f"Sikeresen elhelyezett dobozok: {len(placed)} db")
    print(f"Kimaradt dobozok: {len(unpacked)} db")
    print(f"Térfogat-kihasználtság: {utilization}%")
    print(f"Súlypont-tolerancia rendben? {valid}")

    # Részletek a bepakolt dobozokról
    print("\nMintaként az első néhány doboz pozíciója (X, Y, Z és befoglaló méretek):")
    for p in placed[:71]:
        print(f" - {p.item.id}: X={p.x}, Y={p.y}, Z={p.z} | Méretek: {p.w}x{p.h}x{p.d}")


if __name__ == "__main__":
    run_contour_test()


