n, k = map(int, input().split())
weight_of_goats = list(map(int, input().split()))

def raft_capacity(n, k, weight_of_goats):
    #function checks how many trips are needed
    def trips_needed(capacity):
        goats = sorted(weight_of_goats, reverse=True)
        used = [False] * n
        trips = 0

        i = 0
        while any(not u for u in used):    
            trips += 1
            load = 0
            for j in range(n):
                if not used[j] and load + goats[j] <= capacity:
                    load += goats[j]
                    used[j] = True
        return trips
    
    #setting up a binary search to find the smallest capacity
    min_capacity = max(weight_of_goats)
    max_capacity = sum(weight_of_goats)

    while min_capacity <= max_capacity:
        medium_capacity = (min_capacity + max_capacity) // 2

        if trips_needed(medium_capacity) <= k:
            answer = medium_capacity
            max_capacity = medium_capacity - 1
        else:
            min_capacity = medium_capacity + 1

    return answer 

print(raft_capacity(n, k, weight_of_goats))


