# Routing research

Reference: https://docs.kicad.org/9.0/en/eeschema/eeschema.html (electrical connections and wire junctions). Use exact terminal endpoints, orthogonal segments, and explicit junctions; crossings are not connections. This is engineering reference material, not imported model training data.

Current classifier corpus: 225 synthetic descriptions, including 180 wrapper variations of 20 seed descriptions. Keep related paraphrases together when splitting future train/test sets. Do not report classifier accuracy as routing accuracy.

Next benchmark: separately measure expected versus emitted terminal pairs, fully routed nets, unintended geometric contacts, component-body intersections, true junctions and label-only fallbacks. Test reordered parts, dense layouts, and manual positioning. Reject ambiguous wires rather than claiming complete routing.
