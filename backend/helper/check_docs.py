#!/usr/bin/env python3
import asyncio
from app.models.models import Document
from database import engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def check_docs():
    async with AsyncSession(engine) as session:
        result = await session.execute(select(Document))
        docs = result.scalars().all()
        print(f'Found {len(docs)} documents in database')
        for doc in docs:
            print(f'  - {doc.filename} (ID: {doc.id})')

asyncio.run(check_docs())