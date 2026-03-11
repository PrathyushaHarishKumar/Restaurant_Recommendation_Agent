"""
SENG 691 HW3 - AI Restaurant Recommendation Agent
===================================================
Architecture: Goal-Based + Utility-Based Agent with NLP Query Parsing
Pipeline: NLP → Filter → Rank → Explain
"""

import pandas as pd
import re
import json
import logging
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("RestaurantAgent")


@dataclass
class AgentGoal:
    cuisine:        Optional[str] = None
    location:       Optional[str] = None
    city:           Optional[str] = None
    state:          Optional[str] = None
    party_size:     int = 2
    max_total:      Optional[float] = None
    max_per_person: Optional[float] = None
    day:            Optional[str] = None
    time:           Optional[str] = None
    window_view:    bool = False
    view_types:     list = field(default_factory=list)
    table_for_two:  bool = False
    raw_query:      str = ""


@dataclass
class AgentState:
    step: str = "IDLE"
    total_restaurants: int = 0
    after_cuisine_filter: int = 0
    after_location_filter: int = 0
    after_price_filter: int = 0
    after_hours_filter: int = 0
    after_view_filter: int = 0
    final_count: int = 0
    logs: list = field(default_factory=list)

    def record(self, msg: str):
        self.logs.append(f"[{self.step}] {msg}")
        log.info(msg)


class NLPQueryParser:
    CUISINE_KEYWORDS = {
        "turkish": "Turkish", "italian": "Italian", "japanese": "Japanese",
        "mexican": "Mexican", "american": "American", "french": "French",
        "greek": "Greek Seafood", "indian": "Indian", "seafood": "Seafood",
        "mediterranean": "Mediterranean", "latin": "Latin American",
        "southern": "Southern", "bbq": "BBQ", "asian": "Asian Fusion",
    }

    DAY_KEYWORDS = {
        "monday": "Mon", "tuesday": "Tue", "wednesday": "Wed",
        "thursday": "Thu", "friday": "Fri", "saturday": "Sat", "sunday": "Sun",
        "mon": "Mon", "tue": "Tue", "wed": "Wed", "thu": "Thu",
        "fri": "Fri", "sat": "Sat", "sun": "Sun",
        "tonight": datetime.now().strftime("%a")[:3],
        "today": datetime.now().strftime("%a")[:3],
    }

    NEIGHBORHOODS = [
        "downtown", "inner harbor", "harbor east", "fells point", "canton",
        "federal hill", "mount vernon", "hampden", "roland park", "remington",
        "station north", "clipper mill", "locust point", "port covington",
    ]

    def parse(self, query: str) -> AgentGoal:
        goal = AgentGoal(raw_query=query)
        q = query.lower()
        log.info(f"[NLP] Parsing query: '{query}'")

        for kw, canonical in self.CUISINE_KEYWORDS.items():
            if kw in q:
                goal.cuisine = canonical
                log.info(f"[NLP] Extracted cuisine: {canonical}")
                break

        for nb in self.NEIGHBORHOODS:
            if nb in q:
                goal.location = nb.title()
                log.info(f"[NLP] Extracted neighborhood: {goal.location}")
                break

        if "baltimore" in q:
            goal.city = "Baltimore"
            goal.state = "MD"
            log.info("[NLP] Extracted city: Baltimore, MD")

        party_match = re.search(r'(\d+)\s*(people|person|guests?|party of)', q)
        if party_match:
            goal.party_size = int(party_match.group(1))
        elif "two" in q or "couple" in q:
            goal.party_size = 2
        log.info(f"[NLP] Extracted party size: {goal.party_size}")

        budget_match = re.search(r'under\s*\$?(\d+)|budget[:\s]*\$?(\d+)|less\s+than\s*\$?(\d+)|\$?(\d+)\s*budget', q)
        if budget_match:
            amount = next(x for x in budget_match.groups() if x)
            goal.max_total = float(amount)
            goal.max_per_person = goal.max_total / goal.party_size
            log.info(f"[NLP] Extracted budget: ${goal.max_total} total -> ${goal.max_per_person:.2f}/person")

        for kw, day_abbr in self.DAY_KEYWORDS.items():
            if kw in q:
                goal.day = day_abbr
                log.info(f"[NLP] Extracted day: {day_abbr}")
                break

        time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)', q)
        if time_match:
            hr = int(time_match.group(1))
            mn = int(time_match.group(2) or 0)
            if time_match.group(3) == "pm" and hr != 12:
                hr += 12
            goal.time = f"{hr:02d}:{mn:02d}"
            log.info(f"[NLP] Extracted time: {goal.time}")

        if any(kw in q for kw in ["window", "view", "scenic"]):
            goal.window_view = True
            log.info("[NLP] Window view requested")
        if "garden" in q:
            goal.view_types.append("garden")
        if "street" in q:
            goal.view_types.append("street")
        if "harbor" in q or "waterfront" in q:
            goal.view_types.append("harbor")

        if "table for two" in q or "table for 2" in q:
            goal.table_for_two = True

        return goal


class RestaurantFilterEngine:
    def __init__(self, df: pd.DataFrame, state: AgentState):
        self.df = df.copy()
        self.state = state

    def _day_open(self, open_days_str: str, target_day: str) -> bool:
        s = open_days_str.strip()
        if not target_day:
            return True
        day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        if "-" in s:
            parts = s.split("-")
            if len(parts) == 2:
                try:
                    start = day_order.index(parts[0])
                    end = day_order.index(parts[1])
                    target = day_order.index(target_day)
                    return start <= target <= end
                except ValueError:
                    return True
        return target_day in s

    def _time_open(self, dinner_start: str, dinner_end: str, query_time: str) -> bool:
        if not query_time:
            return True
        try:
            qt = datetime.strptime(query_time, "%H:%M")
            ds = datetime.strptime(dinner_start, "%H:%M")
            de = datetime.strptime(dinner_end, "%H:%M")
            return ds <= qt <= de
        except Exception:
            return True

    def apply_filters(self, goal: AgentGoal) -> pd.DataFrame:
        candidates = self.df.copy()
        self.state.total_restaurants = len(candidates)
        self.state.record(f"Starting with {len(candidates)} total restaurants")

        if goal.cuisine:
            self.state.step = "FILTER:CUISINE"
            candidates = candidates[candidates["cuisine"].str.lower() == goal.cuisine.lower()]
            self.state.after_cuisine_filter = len(candidates)
            self.state.record(f"After cuisine filter ({goal.cuisine}): {len(candidates)} restaurants")

        if goal.location or goal.city:
            self.state.step = "FILTER:LOCATION"
            mask = pd.Series([True] * len(candidates), index=candidates.index)
            if goal.location:
                mask &= (
                    candidates["neighborhood"].str.lower().str.contains(goal.location.lower(), na=False) |
                    candidates["location"].str.lower().str.contains(goal.location.lower(), na=False)
                )
            if goal.city:
                mask &= candidates["city"].str.lower() == goal.city.lower()
            candidates = candidates[mask]
            self.state.after_location_filter = len(candidates)
            self.state.record(f"After location filter ({goal.location}, {goal.city}): {len(candidates)} restaurants")

        if goal.max_per_person:
            self.state.step = "FILTER:PRICE"
            candidates = candidates[candidates["price_per_person"] <= goal.max_per_person]
            self.state.after_price_filter = len(candidates)
            self.state.record(f"After price filter (<=\${goal.max_per_person:.2f}/person): {len(candidates)} restaurants")

        if goal.day or goal.time:
            self.state.step = "FILTER:HOURS"
            def hours_ok(row):
                day_ok = self._day_open(row["open_days"], goal.day) if goal.day else True
                time_ok = self._time_open(row["dinner_start"], row["dinner_end"], goal.time) if goal.time else True
                return day_ok and time_ok
            candidates = candidates[candidates.apply(hours_ok, axis=1)]
            self.state.after_hours_filter = len(candidates)
            self.state.record(f"After hours filter (day={goal.day}, time={goal.time}): {len(candidates)} restaurants")

        if goal.window_view:
            self.state.step = "FILTER:VIEW"
            view_mask = candidates["window_view"].astype(str).str.lower() == "true"
            if goal.view_types:
                type_mask = candidates["view_type"].str.lower().isin([v.lower() for v in goal.view_types])
                view_mask &= type_mask
            candidates = candidates[view_mask]
            self.state.after_view_filter = len(candidates)
            self.state.record(f"After view filter (types={goal.view_types}): {len(candidates)} restaurants")

        if goal.table_for_two:
            self.state.step = "FILTER:TABLE"
            candidates = candidates[candidates["table_for_two"].astype(str).str.lower() == "true"]
            self.state.record(f"After table-for-two filter: {len(candidates)} restaurants")

        self.state.final_count = len(candidates)
        return candidates

    def rank(self, candidates: pd.DataFrame, goal: AgentGoal) -> pd.DataFrame:
        self.state.step = "RANKING"
        if candidates.empty:
            return candidates

        df = candidates.copy()
        df["score_rating"] = (df["rating"] / 5.0) * 40

        if goal.max_per_person:
            df["score_price"] = (1 - (df["price_per_person"] / goal.max_per_person)) * 30
        else:
            df["score_price"] = 15

        df["score_view"] = df["window_view"].astype(str).str.lower().map({"true": 15, "false": 0}).fillna(0)

        max_reviews = df["reviews"].max() if df["reviews"].max() > 0 else 1
        df["score_reviews"] = (df["reviews"] / max_reviews) * 15

        df["total_score"] = (df["score_rating"] + df["score_price"] + df["score_view"] + df["score_reviews"]).round(2)
        df = df.sort_values("total_score", ascending=False).reset_index(drop=True)
        df.index += 1
        self.state.record(f"Ranked {len(df)} restaurants by utility score")
        return df


class ExplanationEngine:
    def explain(self, row: pd.Series, goal: AgentGoal) -> str:
        parts = []

        if goal.location:
            parts.append(f"Location: {row['neighborhood']}, {row['city']}, {row['state']}")

        if goal.cuisine:
            parts.append(f"Cuisine: {row['cuisine']} (matches {goal.cuisine})")

        total_cost = row["price_per_person"] * goal.party_size
        if goal.max_total:
            pct = (total_cost / goal.max_total) * 100
            parts.append(f"Price: ${row['price_per_person']}/person = ${total_cost:.0f} total ({pct:.0f}% of ${goal.max_total:.0f} budget)")
        else:
            parts.append(f"Price: ${row['price_per_person']}/person = ${total_cost:.0f} for {goal.party_size}")

        if goal.day and goal.time:
            parts.append(f"Hours: Open {goal.day} at {goal.time} (serves {row['dinner_start']}-{row['dinner_end']})")

        view_str = str(row.get("window_view", "")).lower()
        if view_str == "true":
            parts.append(f"View: Window view available ({row['view_type']} view)")
        else:
            parts.append("View: No window view listed")

        parts.append(f"Rating: {row['rating']}/5.0 ({row['reviews']:,} reviews)")
        parts.append(f"About: {row['description']}")

        return " | ".join(parts)


class RestaurantAgent:
    """
    Goal-Based + Utility-Based AI Agent for Restaurant Recommendations.

    Pipeline:
      NLP Parser -> Filter Engine -> Ranking Engine -> Explanation Engine
    """

    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path)
        self.parser = NLPQueryParser()
        self.explainer = ExplanationEngine()
        log.info(f"[AGENT] Loaded {len(self.df)} restaurants from {csv_path}")

    def run(self, query: str, top_n: int = 5) -> dict:
        print("\n" + "="*70)
        print("RESTAURANT RECOMMENDATION AGENT - SENG 691 HW3")
        print("="*70)
        print(f"Query: {query}")
        print("="*70 + "\n")

        state = AgentState(step="NLP")

        state.record("Starting NLP query parsing...")
        goal = self.parser.parse(query)
        state.record(
            f"Parsed goal: cuisine={goal.cuisine}, location={goal.location}, "
            f"party={goal.party_size}, budget=${goal.max_total}, "
            f"day={goal.day}, time={goal.time}, "
            f"window={goal.window_view}, views={goal.view_types}"
        )

        state.step = "FILTERING"
        engine = RestaurantFilterEngine(self.df, state)
        filtered = engine.apply_filters(goal)

        if filtered.empty:
            print("\nNo restaurants matched all criteria. Relaxing view filter...\n")
            state.record("No results found - relaxing window view filter")
            goal.window_view = False
            goal.view_types = []
            filtered = engine.apply_filters(goal)

        state.step = "RANKING"
        ranked = engine.rank(filtered, goal)
        top = ranked.head(top_n)

        print("\n" + "-"*70)
        print("PIPELINE SUMMARY")
        print("-"*70)
        print(f"  Total restaurants in DB  : {state.total_restaurants}")
        print(f"  After cuisine filter     : {state.after_cuisine_filter}")
        print(f"  After location filter    : {state.after_location_filter}")
        print(f"  After price filter       : {state.after_price_filter}")
        print(f"  After hours filter       : {state.after_hours_filter}")
        print(f"  After view filter        : {state.after_view_filter}")
        print(f"  Final candidates ranked  : {state.final_count}")
        print(f"  Showing top              : {len(top)}")
        print("-"*70)

        print(f"\nTOP {len(top)} RECOMMENDATIONS\n")
        results = []
        for rank, (_, row) in enumerate(top.iterrows(), 1):
            explanation = self.explainer.explain(row, goal)
            print(f"#{rank}  {row['name']}")
            print(f"    Score: {row['total_score']:.1f}/100")
            print(f"    {explanation}")
            print()
            results.append({
                "rank": rank,
                "name": row["name"],
                "cuisine": row["cuisine"],
                "address": row["address"],
                "price_per_person": float(row["price_per_person"]),
                "total_for_party": float(row["price_per_person"] * goal.party_size),
                "rating": float(row["rating"]),
                "reviews": int(row["reviews"]),
                "window_view": str(row["window_view"]).lower() == "true",
                "view_type": row["view_type"],
                "phone": row["phone"],
                "website": row["website"],
                "score": float(row["total_score"]),
                "explanation": explanation,
            })

        return {
            "query": query,
            "goal": {k: v for k, v in goal.__dict__.items()},
            "pipeline_stats": {
                "total": state.total_restaurants,
                "after_cuisine": state.after_cuisine_filter,
                "after_location": state.after_location_filter,
                "after_price": state.after_price_filter,
                "after_hours": state.after_hours_filter,
                "after_view": state.after_view_filter,
                "final": state.final_count,
            },
            "logs": state.logs,
            "results": results,
        }


if __name__ == "__main__":
    import sys
    import os

    csv_path = os.path.join(os.path.dirname(__file__), "../data/restaurants.csv")
    agent = RestaurantAgent(csv_path)

    default_query = (
        "Find a Turkish restaurant in Downtown Baltimore MD for two people "
        "to have dinner under $65 on Thursday night at 7:30 pm with a table "
        "for two near a window with a view of the garden or the street"
    )

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else default_query
    result = agent.run(query)

    out_file = "agent_output.json"
    with open(out_file, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nFull results saved to {out_file}")
