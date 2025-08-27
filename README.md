## Interactive Travel Guide

New planner on `/travel` lets you enter From, To, Start, End dates and optional interest chips. It calls a backend endpoint `/api/itinerary` which builds a day-wise itinerary using local POIs from `static/data/pois.json` if present.

To add your own places, create:

`static/data/pois.json`

JSON array of objects:

```
[
  {
    "id": "tajmahal",
    "name": "Taj Mahal",
    "city": "Agra",
    "description": "Iconic ivory-white marble mausoleum.",
    "image": "/static/images/tajmahal.jpg",
    "suggestedDurationMin": 120,
    "tags": ["history", "culture"]
  }
]
```

The UI renders animated, selectable cards with hover pop and subtle rotation. Click a card to select it.
# mini_project
3rd semester mini project 
## Team Members : ##
   ### 1) The 'ARYAN' Agarwal ###
   ### 2) Dev 'CR' Saxena ###
   ### 3) Rachit 'Moong_Daal' Kanchan ###
   ### 4) Anurag 'Annu' Singh ###
   ### 5) Rudra 'The Great' Singh ###
