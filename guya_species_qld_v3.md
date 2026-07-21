# Guya — QLD Nature Passport Seed (v3)

**Region tag:** `QLD` (statewide). Supersedes v1–v2.
**Now a multi-domain passport:** fish (catch), marine wildlife (sighting), inland/bush wildlife (sighting), plus bounded collectables (shells/plants).

**Data shape per entry:** `{ name, sci, group, domain, region:'QLD', kind }`
- `kind` = **catch** or **sighting**
- `domain` = `fish` · `marine-wildlife` · `bush-wildlife` · `collectable`
- `group` = the picker dropdown heading (the `##` sections below)

**Two principles that keep this from ballooning**
1. **Generic fallback in every split group** — e.g. "Cod/grouper — unsure", "Shark — unsure", "Stingray — unsure". A fish you can't pin to species still logs cleanly instead of becoming free-text noise.
2. **Seed + grow for open-ended domains** — shells, plants, insects, most birds run to thousands of species. We seed a short "common finds" checklist and let the long tail be photo + free-text, added as you find them. Collection hook, no bloat, no maintenance.

**Design rule held:** names only, no size/keep guidance. Protected + release-by-default species sit under sightings.

---

# FISH — catch (domain: `fish`)

## Bream, Tarwhine & Drummer
| Name | Sci |
|---|---|
| Yellowfin Bream | *Acanthopagrus australis* |
| Pikey Bream | *Acanthopagrus pacificus* |
| Tarwhine | *Rhabdosargus sarba* |
| Luderick | *Girella tricuspidata* |
| Eastern Rock Blackfish (Drummer) | *Girella elevata* |
| Silver Drummer | *Kyphosus sydneyanus* |

## Flathead
| Name | Sci |
|---|---|
| Dusky Flathead | *Platycephalus fuscus* |
| Bartail Flathead | *Platycephalus indicus* |
| Sand/Northern Flathead | *Platycephalus* spp. |
| Flathead — unsure | — |

## Whiting
| Name | Sci |
|---|---|
| Sand (Summer) Whiting | *Sillago ciliata* |
| Trumpeter (Winter) Whiting | *Sillago maculata* |
| Golden-lined Whiting | *Sillago analis* |
| Northern Whiting | *Sillago sihama* |

## Tailor, Dart & Mulloway
| Name | Sci |
|---|---|
| Tailor | *Pomatomus saltatrix* |
| Swallowtail Dart | *Trachinotus coppingeri* |
| Mulloway (Jewfish) | *Argyrosomus japonicus* |
| Mullet (Sea) | *Mugil cephalus* |

## Trevally & Queenfish
| Name | Sci |
|---|---|
| Giant Trevally (GT) | *Caranx ignobilis* |
| Golden Trevally | *Gnathanodon speciosus* |
| Bigeye Trevally | *Caranx sexfasciatus* |
| Brassy Trevally | *Caranx papuensis* |
| Diamond (Pennant) Trevally | *Alectis indica* |
| Queenfish | *Scomberoides commersonnianus* |
| Trevally — unsure | — |

## Mackerel & Tuna (pelagic)
| Name | Sci |
|---|---|
| Spanish Mackerel | *Scomberomorus commerson* |
| Spotted Mackerel | *Scomberomorus munroi* |
| School Mackerel | *Scomberomorus queenslandicus* |
| Grey Mackerel | *Scomberomorus semifasciatus* |
| Longtail Tuna | *Thunnus tonggol* |
| Mackerel Tuna (Mac Tuna) | *Euthynnus affinis* |
| Australian Bonito | *Sarda australis* |

## Kingfish & Cobia
| Name | Sci |
|---|---|
| Yellowtail Kingfish | *Seriola lalandi* |
| Cobia | *Rachycentron canadum* |

## Mangrove Jack & tropical snappers / sea perch
| Name | Sci |
|---|---|
| Mangrove Jack | *Lutjanus argentimaculatus* |
| Fingermark (Golden Snapper) | *Lutjanus johnii* |
| Moses Perch | *Lutjanus russellii* |
| Stripey Snapper | *Lutjanus carponotatus* |
| Red Emperor | *Lutjanus sebae* |
| Crimson Snapper (Nannygai) | *Lutjanus erythropterus* |
| Hussar | *Lutjanus adetii* |
| Snapper (Squire) | *Chrysophrys auratus* |

## Emperors & Sweetlips
| Name | Sci |
|---|---|
| Spangled Emperor | *Lethrinus nebulosus* |
| Red-throat Emperor | *Lethrinus miniatus* |
| Grass Emperor (Grass Sweetlip) | *Lethrinus laticaudis* |
| Long-nose Emperor | *Lethrinus olivaceus* |
| Painted Sweetlip | *Diagramma labiosum* |
| Brown Sweetlip | *Plectorhinchus gibbosus* |
| Emperor/sweetlip — unsure | — |

## Cods & Groupers
| Name | Sci |
|---|---|
| Estuary Cod | *Epinephelus coioides* |
| Malabar (Blackspotted) Cod | *Epinephelus malabaricus* |
| Greasy Rockcod | *Epinephelus tauvina* |
| Flowery Cod | *Epinephelus fuscoguttatus* |
| Maori Cod | *Epinephelus undulatostriatus* |
| Coral Rockcod | *Cephalopholis miniata* |
| Cod/grouper — unsure | — |

## Tuskfish & Wrasse
| Name | Sci |
|---|---|
| Blackspot Tuskfish | *Choerodon schoenleinii* |
| Venus Tuskfish | *Choerodon venustus* |
| Purple Tuskfish | *Choerodon cephalotes* |
| Harlequin Tuskfish | *Choerodon fasciatus* |
| Tuskfish/wrasse — unsure | — |

## Coral Trout & reef
| Name | Sci |
|---|---|
| Coral Trout | *Plectropomus leopardus* |
| Parrotfish | *Scaridae* spp. |
| Surgeonfish | *Acanthuridae* spp. |

## Barramundi, threadfin & estuary sportfish
| Name | Sci |
|---|---|
| Barramundi | *Lates calcarifer* |
| King Threadfin | *Polydactylus macrochir* |
| Blue Threadfin | *Eleutheronema tetradactylum* |
| Tarpon (Oxeye Herring) | *Megalops cyprinoides* |
| Jungle Perch | *Kuhlia rupestris* |

## Freshwater / inland fish (dams, rivers, impoundments)
| Name | Sci |
|---|---|
| Australian Bass | *Percalates novemaculeata* (syn. *Macquaria*) |
| Golden Perch (Yellowbelly) | *Macquaria ambigua* |
| Silver Perch | *Bidyanus bidyanus* |
| Murray Cod | *Maccullochella peelii* |
| Mary River Cod | *Maccullochella mariensis* |
| Saratoga (Southern) | *Scleropages leichardti* |
| Saratoga (Gulf / Northern) | *Scleropages jardinii* |
| Spangled Perch | *Leiopotherapon unicolor* |
| Sleepy Cod | *Oxyeleotris lineolata* |
| Eel-tailed Catfish | *Tandanus tandanus* |
| Forktail Catfish | *Neoarius* spp. |
| Freshwater Mullet | *Trachystoma petardi* |
| Redclaw (crayfish) | *Cherax quadricarinatus* |
| Yabby | *Cherax destructor* |
| Tilapia (introduced) | *Oreochromis mossambicus* |
| European Carp (introduced) | *Cyprinus carpio* |
| Freshwater fish — unsure | — |

*Barramundi, Jungle Perch, Tarpon and Sooty Grunter are freshwater-capable too — they live in the estuary-sportfish / grunter groups above, not duplicated here.*

## Grunter & Javelin
| Name | Sci |
|---|---|
| Barred Javelin | *Pomadasys kaakan* |
| Spotted Javelin | *Pomadasys argenteus* |
| Silver Grunter | *Pomadasys* spp. |
| Sooty Grunter (freshwater) | *Hephaestus fuliginosus* |
| Grunter/javelin — unsure | — |

## Sharks & Rays — catch (mostly release; many no-take — log + return)
| Name | Sci |
|---|---|
| Bull Shark | *Carcharhinus leucas* |
| Common Blacktip Shark | *Carcharhinus limbatus* |
| Blacktip Reef Shark | *Carcharhinus melanopterus* |
| Spinner Shark | *Carcharhinus brevipinna* |
| Hammerhead | *Sphyrna* spp. |
| Wobbegong | *Orectolobus* spp. |
| Eastern Shovelnose Ray | *Aptychotrema rostrata* |
| Giant Shovelnose Ray (Guitarfish) | *Glaucostegus typus* |
| Estuary Stingray | *Hemitrygon fluviorum* |
| Cowtail Stingray | *Pastinachus ater* |
| Blue-spotted Maskray | *Neotrygon* spp. |
| Shark — unsure | — |
| Stingray/ray — unsure | — |

## Crabs & crustaceans (bonus)
| Name | Sci |
|---|---|
| Mud Crab | *Scylla serrata* |
| Blue Swimmer (Sand) Crab | *Portunus armatus* |

---

# WILDLIFE — sighting, marine (domain: `marine-wildlife`, look-don't-take)
| Name | Sci |
|---|---|
| Loggerhead Turtle | *Caretta caretta* |
| Green Turtle | *Chelonia mydas* |
| Hawksbill Turtle | *Eretmochelys imbricata* |
| Flatback Turtle | *Natator depressus* |
| Dugong | *Dugong dugon* |
| Humpback Whale | *Megaptera novaeangliae* |
| Bottlenose Dolphin | *Tursiops* sp. |
| Australian Humpback Dolphin | *Sousa sahulensis* |
| Manta Ray | *Mobula alfredi* |
| Spotted Eagle Ray | *Aetobatus ocellatus* |
| Maori (Humphead) Wrasse — protected | *Cheilinus undulatus* |
| Sea Snake | *Hydrophiinae* spp. |
| Octopus / Cuttlefish | — |

---

# WILDLIFE — sighting, inland / bush (domain: `bush-wildlife`, look-don't-take)
*Bounded "iconic SE/coastal QLD" seed — the rest grows from your photos.*

## Mammals
| Name | Sci |
|---|---|
| Short-beaked Echidna | *Tachyglossus aculeatus* |
| Eastern Grey Kangaroo | *Macropus giganteus* |
| Swamp Wallaby | *Wallabia bicolor* |
| Koala | *Phascolarctos cinereus* |
| Common Brushtail Possum | *Trichosurus vulpecula* |
| Ringtail Possum | *Pseudocheirus peregrinus* |
| Flying-fox | *Pteropus* spp. |

## Reptiles
| Name | Sci |
|---|---|
| Lace Monitor (Goanna) | *Varanus varius* |
| Sand Goanna | *Varanus gouldii* |
| Eastern Water Dragon | *Intellagama lesueurii* |
| Eastern Blue-tongue | *Tiliqua scincoides* |
| Shingleback (Bobtail) | *Tiliqua rugosa* |
| Carpet Python | *Morelia spilota* |
| Eastern Brown Snake | *Pseudonaja textilis* |
| Red-bellied Black Snake | *Pseudechis porphyriacus* |
| Reptile — unsure | — |

## Birds (iconic)
| Name | Sci |
|---|---|
| Laughing Kookaburra | *Dacelo novaeguineae* |
| Rainbow Lorikeet | *Trichoglossus moluccanus* |
| Sulphur-crested Cockatoo | *Cacatua galerita* |
| Galah | *Eolophus roseicapilla* |
| White-bellied Sea-Eagle | *Haliaeetus leucogaster* |
| Osprey | *Pandion haliaetus* |
| Wedge-tailed Eagle | *Aquila audax* |
| Azure Kingfisher | *Ceyx azureus* |

## Frogs
| Name | Sci |
|---|---|
| Green Tree Frog | *Litoria caerulea* |
| Frog — unsure | — |

---

# COLLECTABLES — bounded seed (domain: `collectable`)

## Shells (small "common finds" seed — grows from photos)
Cowrie · Cone shell · Bailer (Melon) shell · Spider Conch · Nautilus · Sand Dollar · Pipi · Turban shell · Murex · Scallop

## Coastal plants (small seed — grows from photos)
Mangrove · Pandanus · Coastal She-oak (Casuarina) · Beach Spinifex · Pigface

---

# Badges (computed locally from the log)
- **First-of-category:** first catch, first marine sighting, first bush sighting, first shell/plant.
- **Count milestones:** 10 / 20 / 50 species (per domain, and overall).
- **Rare / special:** any marine or bush sighting; a protected species (Maori Wrasse); a PB; first-of-species.
- **Local hero:** Mon Repos loggerhead sighting.

---

# Seed-now vs backlog (your call — happy to defer)
**Seed now (in this file):** all fish, marine sightings, bush wildlife (mammals/reptiles/iconic birds/frogs), small shell + plant starters.
**Backlog candidates:** full bird list, insects/spiders, exhaustive shells & plants, freshwater fish beyond the few here, fungi.

**On sourcing (your offer):** for everything above I'm fine — common names verified against Fishes of Australia / Australian Museum. Where your help *would* matter is if we later go exhaustive on shells/plants/birds: a regional checklist export (Atlas of Living Australia for the Bundaberg/Woongarra region, or a field-guide species list) would be the clean source. Grab that if/when we expand those, and I'll verify before it goes in. Not needed for this seed.

**Next:** trim/approve, then I convert to the JSON seed and we wire the picker + passport into the build.
