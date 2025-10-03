def lcs(s1, s2):
    N, M = len(s1)+1, len(s2)+1
    dp = [0]*M
    for i in range(N-2, -1, -1):
        tmp = [0]*M
        for j in range(M-2, -1, -1):
            tmp[j] = 1 + dp[j + 1] if s1[i] == s2[j] else max(dp[j], tmp[j + 1])
        dp = tmp
    return dp[0]
