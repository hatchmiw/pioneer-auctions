// Whole-auction screening policy for Pioneer-style HiBid catalogs.
// This file documents the scoring vocabulary used by screening-master.json.
// Scores route attention only; they are not value estimates or bid recommendations.
export const SIGNALS = [
  {
    "n": "farm",
    "w": 4,
    "s": "tractor|livestock|cattle|horse|dairy|milking|plow|seeder|fenc(?:e|ing)|post[- ]?hole|pitchfork|hoof|wagon|sprayer|garden|chainsaw|weed (?:whip|trimmer)|mower|lawn sweeper"
  },
  {
    "n": "shop",
    "w": 4,
    "s": "wrench|socket|band saw|circular saw|jig saw|reciprocating saw|drill|grinder|sander|clamp|vise|floor jack|bottle jack|puller|welder|welding|torch|compressor|pry bar|hammer|maul|grease gun|hardware|fastener|tool box|wet.?dry vac"
  },
  {
    "n": "auto_trailer",
    "w": 4,
    "s": "trailer|hitch|towing|automotive|battery charger|jumper cable|tire iron|lug wrench|ramp|dolly|hoist|winch"
  },
  {
    "n": "construction",
    "w": 3,
    "s": "electrical|plumbing|pipe wrench|pipe fitting|extension cord|level|ladder|caulk|hinge|insulation|roofing|drywall"
  },
  {
    "n": "storage_handling",
    "w": 2,
    "s": "shelving|locker|organizer bins?|metal carts?|storage cabinets?"
  },
  {
    "n": "food_preservation",
    "w": 3,
    "s": "pressure canner|canning|foodsaver|vacuum sealer|apple peeler|freezer"
  },
  {
    "n": "household_equipment",
    "w": 2,
    "s": "speed queen|washer|dryer|portable air conditioner|kerosene heater"
  },
  {
    "n": "collectible_signal",
    "w": 2,
    "s": "uranium|fenton|fostoria|railroad lantern|john deere|farmall|advertising thermometer|vintage scale"
  }
];
export const THRESHOLDS = {STRONG_TARGET:12,GOOD_OPPORTUNITY:7,PRICE_DEPENDENT:3};
export const POLICY = {
  titleMultiplier:2,
  descriptionMultiplier:1,
  noBidBonus:1,
  lowPriorityPenalty:-5,
  regulatedWeapons:"exclude from recommendation pipeline",
  stage2Required:["STRONG_TARGET","GOOD_OPPORTUNITY","PRICE_DEPENDENT"],
  anomalyAuditIgnorePool:true,
  priceRule:"current bids are observations; only closed realized prices are final auction-price evidence"
};
