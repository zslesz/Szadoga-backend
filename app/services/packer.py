# packer.py
from typing import List
from app.schemas.schema import Container, PlacedItem

"""3D Bin Packing algoritmus megvalósítása First-Fit Decreasing (FFD) heurisztikával."""
class BinPacker3D:

    def __init__(self, container: Container):
        self.container = container
        self.placed_items: List[PlacedItem] = []

    """Visszaadja a doboz lehetséges kiterjedéseit (w, h, d) a forgatási szabályok alapján"""
    def _get_allowed_rotation(self, item) -> list:
        """
        Visszaadja a doboz lehetséges forgatásait, de OKOSAN SORBA RENDEZVE!
        A leglaposabb (legkisebb magasságú) orientációt próbálja először,
        hogy minél kevesebb üres hézag maradjon a rétegek között.
        """
        rotations = []
        if not getattr(item, 'can_rotate', True):
            rotations.append((item.width, item.height, item.depth))
        else:
            # Minden lehetséges 3D forgatás (6 db)
            rotations = [
                (item.width, item.height, item.depth),
                (item.width, item.depth, item.height),
                (item.height, item.width, item.depth),
                (item.height, item.depth, item.width),
                (item.depth, item.width, item.height),
                (item.depth, item.height, item.width)
            ]
            # Kiszűrjük a duplikátumokat (pl. egy szabályos kocka esetén)
            rotations = list(set(rotations))

        # --- TÉRKITÖLTÉS OPTIMALIZÁLÁS (A Titkos Fegyver) ---
        # Rendezzük a forgatásokat:
        # 1. Magasság (h) növekvő sorrendbe (legyen minél laposabb a doboz)
        # 2. Alapterület (w * d) csökkenő sorrendbe (takarjon le minél nagyobb felületet a padlóból)
        # (A rotations listában az elemek: r[0]=w, r[1]=h, r[2]=d)
        rotations.sort(key=lambda r: (r[1], -(r[0] * r[2])))

        return rotations

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

    def _fits_in_container(self, candidate) -> bool:
        """Ellenőrzi, hogy a doboz belefér-e a konténer fizikai határaiba (beleértve a ferde falakat is)."""

        # 1. Alap magasság és mélység ellenőrzés (tető és hátfal)
        if candidate.y + candidate.h > self.container.height:
            return False
        if candidate.z + candidate.d > self.container.depth:
            return False

        # 2. X tengely (szélesség) és Contour ellenőrzés
        if self.container.base_width and self.container.contour_height > 0:

            # A doboz ALJA a legszűkebb keresztmetszet, szigorúan ezt vizsgáljuk!
            if candidate.y < self.container.contour_height:
                progress = candidate.y / self.container.contour_height
                allowed_width = self.container.base_width + (
                            self.container.width - self.container.base_width) * progress
            else:
                # Ha a doboz TELJESEN a ferde fal felett van
                allowed_width = self.container.width

            # Megnézzük, hogy szimmetrikus-e a levágás
            is_double_contoured = "ALF" in self.container.id or "Double" in self.container.name

            if is_double_contoured:
                margin = (self.container.width - allowed_width) / 2.0
                min_x = margin
                max_x = self.container.width - margin
            else:
                # Egyoldalas (AKE) konténer esetén a bal fal egyenes (0), a jobb ferde
                min_x = 0
                max_x = allowed_width

            # Fizikai ütközésvizsgálat a falakkal
            if candidate.x < min_x or (candidate.x + candidate.w) > max_x:
                return False

        else:
            # Szögletes konténer (pl. PMC) esetén a falak egyenesek
            if candidate.x + candidate.w > self.container.width:
                return False

        return True

    def _is_supported(self, candidate) -> bool:
        """Gravitációs ellenőrzés: A ferde falakat (Contour) aktív padlóként kezeli!"""

        # 1. ALAP PADLÓ ELLENŐRZÉS (Y = 0)
        if candidate.y == 0:
            if self.container.base_width and self.container.contour_height > 0:
                box_center_x = candidate.x + (candidate.w / 2.0)
                is_double = "ALF" in self.container.id or "Double" in self.container.name
                if is_double:
                    margin = (self.container.width - self.container.base_width) / 2.0
                    if margin <= box_center_x <= (self.container.width - margin):
                        return True
                    return False
                else:
                    if box_center_x <= self.container.base_width:
                        return True
                    return False
            return True

            # 2. HAGYOMÁNYOS ALÁTÁMASZTÁS DOBOZOK ÁLTAL (25%)
        supported_area = 0.0
        box_base_area = candidate.w * candidate.d

        for p in self.placed_items:
            if abs((p.y + p.h) - candidate.y) < 0.1:
                overlap_x = max(0, min(candidate.x + candidate.w, p.x + p.w) - max(candidate.x, p.x))
                overlap_z = max(0, min(candidate.z + candidate.d, p.z + p.d) - max(candidate.z, p.z))
                if overlap_x > 0 and overlap_z > 0:
                    supported_area += (overlap_x * overlap_z)

        if supported_area >= (box_base_area * 0.10):
            return True

        # 3. ÚJ: FERDE FAL (CONTOUR WEDGE) ALÁTÁMASZTÁS
        # Ha a doboz a ferde részen van, maga a repülőgép törzse (a konténer fala) funkcionál padlóként!
        if self.container.base_width and self.container.contour_height > 0:
            if candidate.y < self.container.contour_height:
                is_double = "ALF" in self.container.id or "Double" in self.container.name
                progress = candidate.y / self.container.contour_height
                allowed_w = self.container.base_width + (self.container.width - self.container.base_width) * progress

                if is_double:
                    left_wall_x = (self.container.width - allowed_w) / 2.0
                    right_wall_x = self.container.width - left_wall_x

                    # Ha a doboz sarka felfekszik a bal vagy jobb ferde falra, a fal megtartja (nincs szükség alsó dobozra!)
                    if abs(candidate.x - left_wall_x) <= 2.0:
                        return True
                    if abs((candidate.x + candidate.w) - right_wall_x) <= 2.0:
                        return True
                else:
                    # Egyoldalas (AKE) konténer esetén csak a jobb oldali ferde fal támaszt
                    if abs((candidate.x + candidate.w) - allowed_w) <= 2.0:
                        return True

        return False

    def _compact_position(self, candidate) -> None:
        """Kétfázisú tömörítés: 5 cm-es sprintek a sebességért, majd 1 cm-es mikrolépések a 80%+ sűrűségért"""
        for step in [5.0, 1.0]:
            moved = True
            while moved:
                moved = False

                # 1. GRAVITÁCIÓ (Lefelé - Y)
                if candidate.y >= step:
                    candidate.y -= step
                    if not self._fits_in_container(candidate) or self._check_overlap(
                            candidate) or not self._is_supported(candidate):
                        candidate.y += step
                    else:
                        moved = True
                        continue

                # 2. BALRA TOLÁS (X)
                if candidate.x >= step:
                    candidate.x -= step
                    if not self._fits_in_container(candidate) or self._check_overlap(
                            candidate) or not self._is_supported(candidate):
                        candidate.x += step
                    else:
                        moved = True
                        continue

                # 3. HÁTRA TOLÁS (Z)
                if candidate.z >= step:
                    candidate.z -= step
                    if not self._fits_in_container(candidate) or self._check_overlap(
                            candidate) or not self._is_supported(candidate):
                        candidate.z += step
                    else:
                        moved = True
                        continue

    """Lefuttatja a pakolási algoritmust a beküldött dobozlistára
    Visszaadja az elhelyezett dobozokat és a kimaradt (nem beférő) dobozokat"""

    def pack(self, items: List):
        # 1. Visszatérünk a Térfogat-alapú (Volume) csökkenő rendezéshez,
        # mert a Best-Fit algoritmussal ez adja a legmagasabb kitöltöttséget (80%+)
        sorted_items = sorted(items, key=lambda i: getattr(i, 'volume', i.width * i.height * i.depth), reverse=True)
        unpacked_items = []

        base_possible_points = []
        if self.container.base_width and self.container.contour_height > 0:
            is_double = "ALF" in self.container.id or "Double" in self.container.name
            if is_double:
                margin = (self.container.width - self.container.base_width) / 2.0
                base_possible_points.append((margin, 0.0, 0.0))
            else:
                base_possible_points.append((0.0, 0.0, 0.0))
        else:
            base_possible_points.append((0.0, 0.0, 0.0))

        for item in sorted_items:
            rotations = self._get_allowed_rotation(item)

            # Set-et használunk a duplikációk elkerülésére (gyorsabb futás)
            pts = set(base_possible_points)

            for p in self.placed_items:
                # Eredeti csúcspontok
                pts.add((p.x + p.w, p.y, p.z))
                pts.add((p.x, p.y + p.h, p.z))
                pts.add((p.x, p.y, p.z + p.d))

                # --- ÚJ LÉPÉS: Projektált (vetített) pontok a mély lyukakhoz ---
                pts.add((p.x + p.w, 0.0, p.z))  # Padlóra vetítve (hogy a padló lyukait kitöltse)
                pts.add((p.x, 0.0, p.z + p.d))  # Padlóra vetítve
                pts.add((0.0, p.y + p.h, p.z))  # Bal falra vetítve

                if self.container.base_width and self.container.contour_height > 0:
                    is_double = "ALF" in self.container.id or "Double" in self.container.name
                    if is_double:
                        top_y = p.y + p.h
                        if top_y < self.container.contour_height:
                            progress = top_y / self.container.contour_height
                            allowed_w = self.container.base_width + (
                                        self.container.width - self.container.base_width) * progress
                            left_wall_x = (self.container.width - allowed_w) / 2.0
                            if left_wall_x < p.x:
                                pts.add((left_wall_x, top_y, p.z))

            possible_points = list(pts)

            # --- JAVÍTOTT BEST-FIT PONTOZÁS ---
            best_candidate = None
            best_score = (float('inf'), float('inf'), float('inf'), float('inf'))

            for x, y, z in possible_points:
                for w, h, d in rotations:
                    candidate = PlacedItem(item=item, x=x, y=y, z=z, w=w, h=h, d=d)

                    if (self._fits_in_container(candidate) and
                            not self._check_overlap(candidate) and
                            self._is_supported(candidate)):

                        self._compact_position(candidate)

                        # A pontozás sorrendje most már megegyezik a gravitációval: Y, X, Z, Magasság
                        score = (candidate.y + candidate.h, candidate.y, candidate.x, candidate.z)

                        if score < best_score:
                            best_score = score
                            best_candidate = candidate

            if best_candidate:
                current_weight = sum(pi.item.weight for pi in self.placed_items) + item.weight
                if current_weight <= self.container.max_weight:
                    self.placed_items.append(best_candidate)
                else:
                    unpacked_items.append(item)
            else:
                unpacked_items.append(item)

        return self.placed_items, unpacked_items

