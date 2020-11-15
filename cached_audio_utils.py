from pyrogram.utils import *


def get_input_file_from_file_id(
        file_id_str: str,
        file_ref: str = None,
        expected_media_type: int = None
) -> Union["raw.types.InputPhoto", "raw.types.InputDocument"]:
    try:
        decoded = decode_file_id(file_id_str)
    except Exception:
        raise ValueError(f"Failed to decode file_id: {file_id_str}")
    else:
        media_type = decoded[0]

        if expected_media_type is not None:
            if media_type != expected_media_type:
                media_type_str = Scaffold.MEDIA_TYPE_ID.get(media_type, None)
                expected_media_type_str = Scaffold.MEDIA_TYPE_ID.get(expected_media_type, None)

                raise ValueError(f'Expected: "{expected_media_type_str}", got "{media_type_str}" file_id instead')

        if media_type in (0, 1, 14):
            raise ValueError(f"This file_id can only be used for download: {file_id_str}")

        if media_type == 2:
            unpacked = struct.unpack("<iiqqqiiii", decoded)
            file_id, access_hash = unpacked[2:4]

            return raw.types.InputPhoto(
                id=file_id,
                access_hash=access_hash,
                file_reference=decode_file_ref(file_ref)
            )

        if media_type in (3, 4, 5, 8, 9, 10, 13):
            unpacked = struct.unpack("<iiqq", decoded)
            file_id, access_hash = unpacked[2:4]

            return raw.types.InputDocument(
                id=file_id,
                access_hash=access_hash,
                file_reference=decode_file_ref(file_ref)
            )

        raise ValueError(f"Unknown media type: {file_id_str}")
