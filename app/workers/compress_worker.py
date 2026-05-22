# # FILE: workers/compress_worker.py
# import asyncio
# from services.queue import compression_queue

# async def start_worker():
#     asyncio.create_task(compression_queue.worker())


# FILE: workers/compress_worker.py
import asyncio
from services.queue import compression_queue

async def main():
    print("Worker started and waiting for tasks...")
    await compression_queue.worker()  # <-- blokuje i działa wiecznie

if __name__ == "__main__":
    asyncio.run(main())
