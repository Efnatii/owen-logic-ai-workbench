# OWEN Logic `.owle` Headless Model Notes

Use this only for headless inspection/generation. It is evidence from local `.owle` files and MCP validation, not a vendor specification.

## Container

- `.owle` is a ZIP container.
- The headless minimum used by `owen_logic_project_create_from_scratch` contains UTF-8 JSON entries named `Project`, `StFunctionBlocks`, and `Visualization`.
- `Project` is a JSON object keyed by document UUID.
- `StFunctionBlocks` and `Visualization` may be empty arrays when the generated project has only FBD documents and no display screens.

## Documents

- Main project wrapper: `DocumentModel`, `ProjectSettingModels`, `ExternalVariableReferences`, `VariableUniqueIdModificators`, `Discriminator=1`.
- Macro wrapper: `DocumentModel`, `Password`, `LastUpdatingId`, `MetaData`, `Discriminator=2`.
- `DocumentModel.DevValue` is the target identifier. For universal PR generation the main document uses an installed PR `DevValue` from `mapVersion.xml`; macro documents use `Macro`.
- `DocumentModel` must carry stable lists for `Elements`, `Variables`, `VariableCatalogSections`, `ConnectorModels`, and `CommentBlockModels`.

## FBD Elements

- An FBD row normally contains `ElementModel`, `Version`, and a top-level `Discriminator`.
- `ElementModel` includes `UniqueId`, `Title`, `Descriptor`, `Location`, `FbType`, `Primitives`, `Ports`, and `ZOrder`.
- Every port `AnchorUniqueId` must reference a primitive UUID inside the same element, unless it is the zero UUID.
- Variable blocks carry top-level `VariableInfoUId`; that UUID must reference exactly one existing `DocumentModel.Variables` row. Reusing one variable UUID for multiple ambiguous variable blocks has caused OWEN Logic runtime errors.
- Observed generic FBD types used by the headless generator:
  - input variable: `FbType=12`, `Discriminator=1`
  - output variable: `FbType=13`, `Discriminator=7`
  - macro input: `FbType=12`, `Discriminator=38`
  - macro output: `FbType=13`, `Discriminator=39`
  - constant: `FbType=30`, `Discriminator=29`
  - NOT/AND/OR/XOR: `FbType=14/5/4/6`, `Discriminator=18`
  - EQ: `FbType=25`, `Discriminator=21`

## Connectors

- Connector row shape: top-level `ConnectorModel` plus `Discriminator=1`.
- `ConnectorModel.FromPortUId` must reference an output port with `PortType=1`.
- `ConnectorModel.ToPortUId` must reference an input port with `PortType=0`.
- Keep one incoming connector per input port unless a deliberate multi-drive experiment is being tested.
- Matching port `DataType` avoids validation warnings.

## Universal PR Generation Boundary

- The universal from-scratch generator creates target-independent FBD variable/logic/constant blocks and macro documents. This is portable across installed PR targets because it does not assume hardware channel layout.
- Physical I/O/module blocks are target-specific. They require installed component catalog evidence plus a compatible project-local archetype, or OWEN Logic's own target migration engine.
- A from-scratch claim is valid only when evidence says `created_new_owle_zip=true`, `copied_existing_owle_as_base=false`, `gui_used=false`, and static validation has zero errors.
