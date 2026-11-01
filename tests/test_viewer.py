import asyncio
import time
import unittest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
import viewer


class ViewerBoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        app=web.Application(middlewares=[viewer.local_only],client_max_size=4096)
        app.add_routes([web.get('/',viewer.page),web.post('/control',viewer.control)])
        self.client=TestClient(TestServer(app))
        await self.client.start_server()
        self.headers={'Host':f'127.0.0.1:{viewer.PORT}','Origin':viewer.URL,'X-iPhone-Control':'1'}
        viewer.last_data=time.monotonic()

    async def asyncTearDown(self):
        await self.client.close()

    async def test_cross_origin_rejected(self):
        h=dict(self.headers,Origin='https://untrusted.example')
        r=await self.client.post('/control',json={'kind':'home'},headers=h)
        self.assertEqual(r.status,403)

    async def test_rebound_host_rejected(self):
        r=await self.client.get('/',headers={'Host':'untrusted.example'})
        self.assertEqual(r.status,403)

    async def test_out_of_range_click_rejected(self):
        r=await self.client.post('/control',json={'kind':'tap','x':1.01,'y':0.5,'aspect':0.56},headers=self.headers)
        self.assertEqual(r.status,400)

    async def test_stale_picture_disables_input(self):
        viewer.last_data=0
        r=await self.client.post('/control',json={'kind':'home'},headers=self.headers)
        self.assertEqual(r.status,503)

    async def test_parallel_input_rejected(self):
        async with viewer.input_lock:
            r=await self.client.post('/control',json={'kind':'home'},headers=self.headers)
        self.assertEqual(r.status,409)

    async def test_frame_embedding_disallowed(self):
        r=await self.client.get('/',headers=self.headers)
        self.assertEqual(r.status,200)
        self.assertEqual(r.headers['X-Frame-Options'],'DENY')
        self.assertIn("frame-ancestors 'none'",r.headers['Content-Security-Policy'])

if __name__=='__main__': unittest.main()
