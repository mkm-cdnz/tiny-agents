import unittest, tempfile, base64
from pathlib import Path
import server

class DemoTests(unittest.TestCase):
    def test_photo_prompt_answer_are_retained(self):
        with tempfile.TemporaryDirectory() as d:
            store = server.Store(Path(d))
            record = store.create('Describe this', 'qwen3.5:9b', b'\xff\xd8\xffexample', 'image/jpeg')
            store.finish(record['id'], 'A test image', None)
            found = store.get(record['id'])
            self.assertEqual(found['answer'], 'A test image')
            self.assertEqual(found['prompt'], 'Describe this')
            self.assertEqual(found['status'], 'done')
            self.assertEqual((Path(d) / found['photo']).read_bytes(), b'\xff\xd8\xffexample')

if __name__ == '__main__': unittest.main()
