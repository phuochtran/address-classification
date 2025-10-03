def edit_distance(word1, word2):
    n, m = len(word1), len(word2)
    dp = [[0 for _ in range(m+1)] for _ in range(n+1)]
    for i in range(n):
        dp[i][m] = len(word1) - i
    for j in range(m):
        dp[n][j] = len(word2) - j
    for i in range(n-1, -1, -1):
        for j in range(m-1, -1, -1):
            dp[i][j] = dp[i+1][j+1] if word1[i] == word2[j] else 1 + min([dp[i][j+1], dp[i+1][j], dp[i+1][j+1]])
    return dp[0][0]
