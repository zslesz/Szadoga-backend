# packer.py
from typing import List, Tuple, Optional
from uld_packing_core.models import Item, Container, PlacedItem
from uld_packing_core.solver import WeightAndBalanceEngine
import itertools

"""3D Bin Packing algoritmus megvalósítása First-Fit Decreasing (FFD) heurisztikával."""
class BinPacker3D:

    def __init__(self, container: Container):
        self.container = container
        self.placed_items: List[PlacedItem] = []

    """Visszaadja a doboz lehetséges kiterjedéseit (w, h, d) a forgatási szabályok alapján"""
    def _get_allowed_rotation(self, item : Item) -> List[Tuple[float, float, float]]:
        if not item.can_rotate:
            return [(item.width, item.height, item.depth)]
        """Minden lehetséges permutáció"""
        dimensions = [item.width, item.height, item.depth]

        return list(set(itertools.permutations(dimensions)))

    """Ellenőrzi, hogy a tesztelt doboz ütközik-e bármelyik már elhelyezett dobozzal."""
    def _check_overlap(self, candidate: PlacedItem) -> bool:
        cx1, cy1, cz1 = candidate.x, candidate.y, candidate.z
        cx2, cy2, cz2 = cx1 + candidate.w, cy1 + candidate.h, cz1 + candidate.d

        for placed in self.placed_items:
            px1, py1, pz1 = placed.x, placed.y, placed.z
            px2, py2, pz2 = px1 + placed.w, py1 + placed.h, pz1 + placed.d

            """Ha mindhárom tengelyen átfedés van, akkor ütköznek"""
            overlap_x = (cx1 < px2) and (cx2 > px1)
            overlap_y = (cy1 < py2) and (cy2 > py1)
            overlap_z = (cz1 < pz2) and (cz2 > pz1)

            if overlap_x and overlap_y and overlap_z:
                """Ütközés van"""
                return True
        return False

    """Ellenőrzi, hogy a doboz belóg-e a konténer fizikai korlátai közé beleértve a contourt is."""
    def _fits_in_container(self, candidate: PlacedItem) -> bool:

        """Konténer határok ellenőrzése"""
        if candidate.y + candidate.h > self.container.height:
            return False
        if candidate.z + candidate.d > self.container.depth:
            return False

        """Az x tengely (szélesség) ellenőrzése a contour figyelembevételével"""
        """Ha a konténer rendelkezik ferde alső résszel"""
        if self.container.base_width and self.container.contour_height > 0:

            """Doboz alja és teteje megvizsgálása"""
            """A doboz legmasagass pontján lévő szélesség határt nézzük"""
            box_top_y = candidate.y + candidate.h

            if box_top_y <= self.container.contour_height:
                progress = box_top_y / self.container.contour_height
                allowed_width = self.container.base_width + (self.container.width - self.container.base_width) * progress
            else:
                allowed_width = self.container.width
            if candidate.x + candidate.w > allowed_width:
                return False
        else:
            """Ha a konténer szögletes"""
            if candidate.x + candidate.w > self.container.width:
                return False
        return True


    """Lefuttatja a pakolási algoritmust a beküldött dobozlistára
    Visszaadja az elhelyezett dobozokat és a kimaradt (nem beférő) dobozokat"""
    def pack(self, items: List[Item]) -> Tuple[List[PlacedItem], List[Item]]:
        """1. Rendezés térfogat szerint csökkenő sorrendbe (First-Fit Decreasing)"""
        sorted_items = sorted(items, key=lambda i: i.volume, reverse=True)
        unpacked_items: List[Item] = []

        for item in sorted_items:
            packed = False
            rotations = self._get_allowed_rotation(item)

            """Megvizsgáljuk a lehetséges bepakolási pontokat (Pivot points)
            Alapesetben a konténer sarkai és a már elhelyezett dobozok csúcsai/szélei"""
            possible_points = [(0.0, 0.0, 0.0)]
            for p in self.placed_items:
                possible_points.append((p.x + p.w, p.y, p.z))
                possible_points.append((p.x, p.y + p.h, p.z))
                possible_points.append((p.x, p.y, p.z + p.d))

            """Rendezzük a pontokat (alulról felfelé, hátulról előre, balról jobbra)"""
            possible_points = sorted(possible_points, key=lambda pt: (pt[2], pt[1], pt[0]))

            for x, y, z in possible_points:
                if packed: break

                for w, h, d in rotations:
                    candidate = PlacedItem(item=item, x=x, y=y, z=z, w=w, h=h, d=d)

                    if self._fits_in_container(candidate) and not self._check_overlap(candidate):
                        current_weight =  sum(pi.item.weight for pi in self.placed_items) + item.weight
                        if current_weight <= self.container.max_weight:
                            self.placed_items.append(candidate)
                            packed = True
                            break

            if not packed:
                unpacked_items.append(item)

        return self.placed_items, unpacked_items

"""Teszt"""
if __name__ == "__main__":
    import random

    """Konténer létrehozása"""
    container = Container(
        id="ULD-LD3",
        name="Standard LD3 Container",
        width=150.0,
        height=150.0,
        depth=160.0,
        max_weight=1500.0,
        cog_target_x=75.0,
        cog_target_y=75.0,
        cog_target_z=80.0
    )

    """Teszt doboz generálás"""
    test_items = []
    for i in range(1, 51):
        test_items.append(
            Item(
                id=f"BOX-{i}",
                width=random.choice([30.0, 40.0, 50.0]),
                height=random.choice([30.0, 40.0, 50.0]),
                depth=random.choice([30.0, 40.0, 50.0]),
                weight=round(random.uniform(10.0, 50.0), 1)
            )
        )

    packer = BinPacker3D(container)
    placed, unpacked = packer.pack(test_items)

    """Súlypont ellenőrzés"""
    valid, cog_metrics = WeightAndBalanceEngine.is_cog_valid(container, placed)

    """Térfogat-kihasználtság kiszámítása"""
    total_packed_volume = sum(p.item.volume for p in placed)
    utilization_pct = round((total_packed_volume / container.max_volume) * 100, 2)

    print("=== 3D BIN PACKING TESZT EREDMÉNYEK ===")
    print(f"Összes doboz: {len(test_items)} db")
    print(f"Sikeresen elhelyezve: {len(placed)} db")
    print(f"Kimaradt: {len(unpacked)} db")
    print(f"Térfogat-kihasználtság: {utilization_pct}%")
    print(f"Eredő Súlypont (X, Y, Z): ({cog_metrics['cog_x']}, {cog_metrics['cog_y']}, {cog_metrics['cog_z']})")
    print(f"Súlypont-tolerancia rendben? {valid}")