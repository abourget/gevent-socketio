#Returns up to ARGV[2] keys with values less than ARGV[1] across all hashes given in KEYS
LUA_BUCKETS_FILTER_LT = """
    local bulk, id, value, result, count, limit

    result = {}
    count = 0
    value = tonumber(ARGV[1])
    limit = tonumber(ARGV[2] or 100)
    
    for ki, key in ipairs(KEYS) do
      bulk = redis.call('hgetall', key)
      for i, v in ipairs(bulk) do
        if i % 2 == 1 then
          id = v
        elseif tonumber(v) < value then
          table.insert(result, id)
          count = count + 1
          if count >= limit then
            return result
          end
        end
      end
    end
    
    return result
"""

#Deletes the hashed value from the bucket and removes empty buckets from the set of bucket names
LUA_BUCKET_HDEL = """
local result = redis.call('hdel', KEYS[1], ARGV[1])
if redis.call('hlen', KEYS[1]) < 1 then
  redis.call('srem', KEYS[2], KEYS[1])
end
return result
"""