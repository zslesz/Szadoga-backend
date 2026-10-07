from typing import List, Tuple, Dict
from app.schemas.schema import Container, PlacedItem

class WeightAndBalanceEngine:
    @staticmethod
    def calculate_cog(placed_items: List[PlacedItem]) -> Tuple[float, float, float]:
        """Elhelyezett dobozok eredo sulypontja"""
        if not placed_items:
            return (0.0, 0.0, 0.0)
        total_weight = sum(pi.item.weight for pi in placed_items)
        if total_weight == 0:
            return (0.0, 0.0, 0.0)

        """Nyomaték számítás"""
        weighted_x = sum(pi.item.weight * pi.center_of_mass[0] for pi in placed_items)
        weighted_y = sum(pi.item.weight * pi.center_of_mass[1] for pi in placed_items)
        weighted_z = sum(pi.item.weight * pi.center_of_mass[2] for pi in placed_items)

        cog_x = weighted_x / total_weight
        cog_y = weighted_y / total_weight
        cog_z = weighted_z / total_weight

        return (round(cog_x, 2), round(cog_y, 2), round(cog_z, 2))

    @staticmethod
    def is_cog_valid(container : Container, placed_items : List[PlacedItem]) -> Tuple[bool, Dict[str, float]]:
        """Belefer e a sulypont a tolernaciaba"""

        cog_x , cog_y , cog_z = WeightAndBalanceEngine.calculate_cog(placed_items)

        diff_x = abs(cog_x - container.cog_target_x)
        diff_y = abs(cog_y - container.cog_target_y)
        diff_z = abs(cog_z - container.cog_target_z)

        is_valid = (
            diff_x <= container.cog_tolerance_x and
            diff_y <= container.cog_tolerance_y and
            diff_z <= container.cog_tolerance_z
        )


        metrics = {
            "cog_x": cog_x,
            "cog_y": cog_y,
            "cog_z": cog_z,
            "diff_x": round(diff_x, 2),
            "diff_y": round(diff_y, 2),
            "diff_z": round(diff_z, 2),
            "is_valid": is_valid
        }

        return is_valid, metrics
