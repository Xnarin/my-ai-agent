n = 5
m = 5

snail = [[0 for j in range(m)] for i in range(n)]
 
di = [0, 1, 0, -1] # 우 하 좌 상
dj = [1, 0, -1, 0] # 1이 위 2가 아래 3이 오른쪽 4가 왼쪽
# 일단 0,0 이 시작인데 위에가 막혀잇잖아. 오른쪽 이동
# 옆이 막혀잇어. 밑으로이동
# 밑에가 막힘 왼족이동


num = 1
i = 0
j = 0

d = 0

for _ in range(n * m):
    snail[i][j] = num
    num += 1

    ni = i + di[d]
    nj = j + dj[d]

    if not (0 <= ni < n and 0 <= nj < m) or snail[ni][nj] != 0:
        d = (d + 1) % 4
        ni = i + di[d]
        nj = j + dj[d]

    i = ni
    j = nj

pprint(snail)


