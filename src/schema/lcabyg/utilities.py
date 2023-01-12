"""Module with utilities for translating schema to LCAByg."""
import logging
from enum import Enum

from models.schema_category import SchemaCategory
from models.schema_element import SchemaElement

logger = logging.getLogger(__name__)


class EntityTypes(Enum):
    CONSTRUCTION = "Construction"
    ELEMENT = "Element"
    PHASE = NotImplementedError
    PRODUCT = NotImplementedError


class Units(Enum):
    AREA = "M2"
    LENGTH = "M"
    MASS = "KG"
    NONE = "Pcs"
    VOLUME = "M3"


def _translate_bim7aa_to_gendk(
    entity: SchemaCategory | SchemaElement,
) -> str:
    """Translate from BIM7AA to LCAByg category.

    Falls back to 'Other' if category does not exist.
    """
    if isinstance(entity, SchemaElement):
        type_id = entity.schema_category.name.split("|")[0].strip()
    else:
        type_id = entity.name.split("|")[0].strip()

    return _bim7aa_to_gendk_dict.get(str(type_id), "069983d0-d08b-405b-b816-d28ca9648956")


CATEGORY_RESOLVERS = {"BIM7AA": _translate_bim7aa_to_gendk}

"""ATTENTION: The translation from BIM7AA to LCAByg is not lossless."""
_bim7aa_to_gendk_dict = {
    "103": "3680fa33-81cb-4681-96cc-86948ad19ba0",
    "121": "1a966c7c-fd7c-4abc-9d4b-307fdcd0cc88",
    "122": "e5f1c0f4-431e-4722-919f-35b15793f061",
    "123": "e582a92e-71d6-4137-89ab-2870dec4a475",
    "124": "069983d0-d08b-405b-b816-d28ca9648956",
    "125": "e582a92e-71d6-4137-89ab-2870dec4a475",
    "126": "270e865a-07e6-4dbd-b4ff-a5e90edeba60",
    "131": "2ffe16fd-f0c9-4d31-a31a-f96d58d3df95",
    "181": "d4beed46-bf57-49c7-a57f-a9bdf42484a5",
    "182": "069983d0-d08b-405b-b816-d28ca9648956",
    "205": "1caeddce-29e9-4067-b85b-36e8d103a4a0",
    "211": "10a52123-48d7-466a-9622-d463511a6df0",
    "212": "10a52123-48d7-466a-9622-d463511a6df0",
    "213": "10a52123-48d7-466a-9622-d463511a6df0",
    "214": "10a52123-48d7-466a-9622-d463511a6df0",
    "215": "10a52123-48d7-466a-9622-d463511a6df0",
    "216": "10a52123-48d7-466a-9622-d463511a6df0",
    "217": "10a52123-48d7-466a-9622-d463511a6df0",
    "218": "10a52123-48d7-466a-9622-d463511a6df0",
    "221": "59ab59a5-2482-45ae-85f1-d0e39e640712",
    "222": "59ab59a5-2482-45ae-85f1-d0e39e640712",
    "223": "59ab59a5-2482-45ae-85f1-d0e39e640712",
    "224": "a9ab6709-61e1-46c1-a2e8-df00bdd0bb91",
    "225": "a9ab6709-61e1-46c1-a2e8-df00bdd0bb91",
    "226": "a9ab6709-61e1-46c1-a2e8-df00bdd0bb91",
    "231": "f4c234ec-77f1-4ee0-92d0-f1819e0307d4",
    "232": "f4c234ec-77f1-4ee0-92d0-f1819e0307d4",
    "233": "f4c234ec-77f1-4ee0-92d0-f1819e0307d4",
    "234": "f4c234ec-77f1-4ee0-92d0-f1819e0307d4",
    "239": "f4c234ec-77f1-4ee0-92d0-f1819e0307d4",
    "241": "1caeddce-29e9-4067-b85b-36e8d103a4a0",
    "242": "1caeddce-29e9-4067-b85b-36e8d103a4a0",
    "243": "1caeddce-29e9-4067-b85b-36e8d103a4a0",
    "244": "1caeddce-29e9-4067-b85b-36e8d103a4a0",
    "245": "1caeddce-29e9-4067-b85b-36e8d103a4a0",
    "246": "1caeddce-29e9-4067-b85b-36e8d103a4a0",
    "251": "ec9ee040-9c1d-4cae-864c-4c6a0e4b8c5b",
    "252": "ec9ee040-9c1d-4cae-864c-4c6a0e4b8c5b",
    "253": "ec9ee040-9c1d-4cae-864c-4c6a0e4b8c5b",
    "254": "ec9ee040-9c1d-4cae-864c-4c6a0e4b8c5b",
    "255": "506a420e-c3cd-4849-a759-3117f10937b1",
    "256": "506a420e-c3cd-4849-a759-3117f10937b1",
    "257": "506a420e-c3cd-4849-a759-3117f10937b1",
    "259": "506a420e-c3cd-4849-a759-3117f10937b1",
    "261": "a48092d1-8b5c-4fa9-9ada-69cec3fd1dca",
    "262": "a48092d1-8b5c-4fa9-9ada-69cec3fd1dca",
    "263": "a48092d1-8b5c-4fa9-9ada-69cec3fd1dca",
    "271": "d734712a-d27d-42c5-936f-98fe4c4df90b",
    "272": "d734712a-d27d-42c5-936f-98fe4c4df90b",
    "273": "d734712a-d27d-42c5-936f-98fe4c4df90b",
    "274": "d734712a-d27d-42c5-936f-98fe4c4df90b",
    "275": "d734712a-d27d-42c5-936f-98fe4c4df90b",
    "276": "d734712a-d27d-42c5-936f-98fe4c4df90b",
    "279": "d734712a-d27d-42c5-936f-98fe4c4df90b",
    "302": "1caeddce-29e9-4067-b85b-36e8d103a4a0",
    "311": "9bd14e05-5fba-4ecb-ab41-7940a8a0dbdc",
    "312": "dcbf55db-3189-4d22-9b2b-2e27c057b363",
    "313": "9bd14e05-5fba-4ecb-ab41-7940a8a0dbdc",
    "315": "dcbf55db-3189-4d22-9b2b-2e27c057b363",
    "316": "10a52123-48d7-466a-9622-d463511a6df5",
    "317": "10a52123-48d7-466a-9622-d463511a6df0",
    "319": "10a52123-48d7-466a-9622-d463511a6df0",
    "321": "9bd14e05-5fba-4ecb-ab41-7940a8a0dbdc",
    "322": "dcbf55db-3189-4d22-9b2b-2e27c057b363",
    "323": "9bd14e05-5fba-4ecb-ab41-7940a8a0dbdc",
    "325": "dcbf55db-3189-4d22-9b2b-2e27c057b363",
    "326": "9bd14e05-5fba-4ecb-ab41-7940a8a0dbdc",
    "327": "a9ab6709-61e1-46c1-a2e8-df00bdd0bb91",
    "329": "a9ab6709-61e1-46c1-a2e8-df00bdd0bb91",
    "331": "bf2534e2-87e6-40cb-9fff-17fb3d85a52a",
    "332": "bf2534e2-87e6-40cb-9fff-17fb3d85a52a",
    "334": "bf2534e2-87e6-40cb-9fff-17fb3d85a52a",
    "335": "bf2534e2-87e6-40cb-9fff-17fb3d85a52a",
    "336": "bf2534e2-87e6-40cb-9fff-17fb3d85a52a",
    "341": "1caeddce-29e9-4067-b85b-36e8d103a4a0",
    "342": "1caeddce-29e9-4067-b85b-36e8d103a4a0",
    "351": "a77a1779-8794-48bf-9e80-2c0a8bb36596",
    "352": "a77a1779-8794-48bf-9e80-2c0a8bb36596",
    "353": "a77a1779-8794-48bf-9e80-2c0a8bb36596",
    "354": "a77a1779-8794-48bf-9e80-2c0a8bb36596",
    "355": "a77a1779-8794-48bf-9e80-2c0a8bb36596",
    "356": "a77a1779-8794-48bf-9e80-2c0a8bb36596",
    "357": "a77a1779-8794-48bf-9e80-2c0a8bb36596",
    "361": "bdbec7c1-4744-43f8-9d06-84cf75288110",
    "371": "d734712a-d27d-42c5-936f-98fe4c4df90b",
    "372": "dcbf55db-3189-4d22-9b2b-2e27c057b363",
    "373": "dcbf55db-3189-4d22-9b2b-2e27c057b363",
    "376": "d734712a-d27d-42c5-936f-98fe4c4df90b",
    "411": "10a52123-48d7-466a-9622-d463511a6df0",
    "412": "10a52123-48d7-466a-9622-d463511a6df0",
    "413": "10a52123-48d7-466a-9622-d463511a6df0",
    "421": "a9ab6709-61e1-46c1-a2e8-df00bdd0bb91",
    "422": "a9ab6709-61e1-46c1-a2e8-df00bdd0bb91",
    "423": "a9ab6709-61e1-46c1-a2e8-df00bdd0bb91",
    "431": "bf2534e2-87e6-40cb-9fff-17fb3d85a52a",
    "432": "bf2534e2-87e6-40cb-9fff-17fb3d85a52a",
    "433": "bf2534e2-87e6-40cb-9fff-17fb3d85a52a",
    "441": "1caeddce-29e9-4067-b85b-36e8d103a4a0",
    "442": "1caeddce-29e9-4067-b85b-36e8d103a4a0",
    "443": "1caeddce-29e9-4067-b85b-36e8d103a4a0",
    "451": "a77a1779-8794-48bf-9e80-2c0a8bb36596",
    "452": "a77a1779-8794-48bf-9e80-2c0a8bb36596",
    "453": "a77a1779-8794-48bf-9e80-2c0a8bb36596",
    "461": "a48092d1-8b5c-4fa9-9ada-69cec3fd1dca",
    "462": "a48092d1-8b5c-4fa9-9ada-69cec3fd1dca",
    "463": "a48092d1-8b5c-4fa9-9ada-69cec3fd1dca",
    "471": "f4c234ec-77f1-4ee0-92d0-f1819e0307d4",
    "472": "f4c234ec-77f1-4ee0-92d0-f1819e0307d4",
    "531": "16528722-ecc6-4a69-a269-35ba3e1205b2",
    "552": "cf702d99-5d5a-4973-ba9c-c4dbfae656a9",
    "553": "cf702d99-5d5a-4973-ba9c-c4dbfae656a9",
    "561": "0fb0348e-2c54-40cb-a4c6-a9c1f2033b22",
    "562": "aea37dbf-bc04-404c-af3e-7f12d7f626b2",
    "563": "0fb0348e-2c54-40cb-a4c6-a9c1f2033b22",
    "571": "58015317-c3ee-41d3-a9df-5fbea8fb2dd2",
    "572": "cf702d99-5d5a-4973-ba9c-c4dbfae656a9",
    "574": "cf702d99-5d5a-4973-ba9c-c4dbfae656a9",
    "578": "58015317-c3ee-41d3-a9df-5fbea8fb2dd2",
    "591": "069983d0-d08b-405b-b816-d28ca9648956",
    "592": "069983d0-d08b-405b-b816-d28ca9648956",
    "593": "069983d0-d08b-405b-b816-d28ca9648956",
    "598": "895bc4b9-ac42-46c2-8b6b-52a031660614",
    "681": "97145af4-423d-447f-a76e-b26feba645cd",
    "801": "14bdd9bc-fc11-4846-b89d-5434dd04b773",
    "802": "14bdd9bc-fc11-4846-b89d-5434dd04b773",
    "803": "14bdd9bc-fc11-4846-b89d-5434dd04b773",
    "804": "14bdd9bc-fc11-4846-b89d-5434dd04b773",
    "805": "14bdd9bc-fc11-4846-b89d-5434dd04b773",
    "816": "d734712a-d27d-42c5-936f-98fe4c4df90b",
    "817": "d734712a-d27d-42c5-936f-98fe4c4df90b",
}
