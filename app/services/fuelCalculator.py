class FuelCalculator:
    @staticmethod
    def calculate(distance_km: float, payload_kg: float, profile) -> dict:
        """Kiszámolja a kerozinfogyasztást a gép profilja és a terhelés alapján."""

        # 1. Hasznos teher átváltása tonnába
        payload_tonnes = payload_kg / 1000.0

        # 2. Repülési idő számítása
        est_time_hours = distance_km / profile.speed_kmh
        hours = int(est_time_hours)
        minutes = round((est_time_hours - hours) * 60)

        # 3. Aktuális fogyasztás
        current_burn_rate = profile.base_burn_kgh + (payload_tonnes * profile.penalty_per_tonne)

        # 4. Üzemanyag összetevők
        trip_fuel = est_time_hours * current_burn_rate
        contingency_fuel = trip_fuel * 0.05

        # --- ÚJ LOGIKA: Dinamikus Állandó Tartalék ---
        # Kiszámoljuk, hányszorosára nőtt a gép fogyasztása az üres állapothoz képest.
        # Pl. ha 8000 kg/h az alap, de most 12690 kg/h a teher miatt, akkor a szorzó ~1.58
        burn_ratio = current_burn_rate / profile.base_burn_kgh

        # A tartalékot felszorozzuk ezzel az aránnyal (így a nehezebb gép tartaléka is több lesz)
        dynamic_reserve = profile.reserve_fuel_kg * burn_ratio

        # Összesítés
        total_fuel = trip_fuel + contingency_fuel + dynamic_reserve

        return {
            "speed_kmh": profile.speed_kmh,
            "base_burn_kgh": profile.base_burn_kgh,
            "penalty_per_tonne": profile.penalty_per_tonne,
            "est_time_hours": round(est_time_hours, 2),
            "hours": hours,
            "minutes": minutes,
            "current_burn_rate": round(current_burn_rate, 2),
            "trip_fuel": round(trip_fuel, 2),
            "contingency_fuel": round(contingency_fuel, 2),
            "reserve_fuel": round(dynamic_reserve, 2),
            "total_fuel": round(total_fuel, 2)
        }