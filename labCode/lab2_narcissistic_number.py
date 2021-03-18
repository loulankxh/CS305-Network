def find_narcissistic_number(start: int, end: int):
    result = []
    x = start
    while start <= x < end:
        y = str(x)
        z = 0
        k = len(y)
        for i in range(k):
            z += int(y[i]) ** k
        if z == x:
            result.append(x)
        x += 1
    return result


# if __name__ == "__main__":
#     str = "abcdefd"
#     print(str[1:3])