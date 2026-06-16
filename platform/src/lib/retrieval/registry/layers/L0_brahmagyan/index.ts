/**
 * Layer L0_brahmagyan — Wave 3 R2: register all L0 retrieval capabilities
 * Existing: asset_registry resources + entity tools
 * Added: 4 corpus query tools (yoga/dosha/remedy/classical texts)
 */
import { registerCapability } from '../../index'

import { assetRegistryL0Capability }  from './asset_registry_l0'
import { assetRegistryAllCapability } from './asset_registry_all'
import { listEntitiesCapability }     from './list_entities'
import { resolveEntityCapability }    from './resolve_entity'
import { intentClassifyCapability }   from './intent_classify'
import { queryYogaCatalogCapability } from './query_yoga_catalog'
import { queryDoshaCatalogCapability} from './query_dosha_catalog'
import { queryRemedyCorpusCapability} from './query_remedy_corpus'
import { queryClassicalTextsCapability } from './query_classical_texts'

registerCapability(assetRegistryL0Capability)
registerCapability(assetRegistryAllCapability)
registerCapability(listEntitiesCapability)
registerCapability(resolveEntityCapability)
registerCapability(intentClassifyCapability)
registerCapability(queryYogaCatalogCapability)
registerCapability(queryDoshaCatalogCapability)
registerCapability(queryRemedyCorpusCapability)
registerCapability(queryClassicalTextsCapability)
