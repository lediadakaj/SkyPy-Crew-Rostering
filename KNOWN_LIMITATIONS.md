## Known Limitations & Future Improvements

This project is built to meet the assignment requirements in a clear and simple way. It avoids unnecessary complexity, but there are still a few areas that could be improved.



### 1. Greedy Scheduling Approach

The scheduler works in a greedy way, it goes through flights in `(priority, departure)` order and assigns the first valid Captain and First Officer it finds.

This keeps things simple and predictable, and it works fine for the given data. The downside is that it doesn’t look ahead. A decision that seems fine at the moment can sometimes block better choices later, which may lead to some flights staying unassigned.

A better approach could try different combinations before locking in a decision.



### 2. No Cost-Based Decisions

The system calculates layover costs, but it doesn’t use them when making assignments. If several crew members are valid for a flight, it just picks the first one it finds.

That means the schedule is correct, but not necessarily the cheapest or most efficient.

An improvement would be to prefer lower-cost crew or try to reduce total cost across the schedule.



### 3. In-Memory State

The latest schedule is stored in memory inside the Flask app.

This keeps the setup simple, but it also means:

* data is lost if the app restarts,
* it doesn’t work well with multiple workers,
* and it doesn’t scale easily.

In a real system, this would usually be stored in a database or something like Redis.



### 4. Limited Rules

Only the main rules from the assignment are implemented:

* range limits,
* home base requirement,
* route continuity,
* and rest rules.

It may have many more rules, like duty hour limits, regulations, aircraft qualifications, and crew preferences.



### 5. No History

The API only keeps the latest result. Every new run replaces the previous one.

So there’s no way to look back at old schedules or compare runs.



### 6. No Backtracking

Once the scheduler makes a decision, it doesn’t go back and change it.

This makes it fast and easy to follow, but not always optimal. A more advanced version could try different options and go back if something doesn’t work later, to find better overall schedules.
