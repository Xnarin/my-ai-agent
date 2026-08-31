import asyncio


async def async_work(name: str, seconds: int) -> str:
    print(name, "시작")
    await asyncio.sleep(seconds)
    print(name, "완료")
    return f"{name} 결과"


async def main():
    results = await asyncio.gather(
        async_work("작업 A", 1),
        async_work("작업 B", 1),
        async_work("작업 C", 1),
    )
    print("결과:", results)


async def f():
    await main

if __name__ == "__main__":
    asyncio.run(main())