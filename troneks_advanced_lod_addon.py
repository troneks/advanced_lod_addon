bl_info = {
    "name": "Custom LOD Generator",
    "author": "Troneks",
    "version": (5, 1),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > LOD Generator",
    "description": "An advanced tool for generating Levels of Detail (LOD) with custom settings and multi-language support.",
    "category": "Object",
}

import bpy
import bmesh
import locale
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import (
    FloatProperty,
    IntProperty,
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    StringProperty,
)
from mathutils import Vector

translations = {
    'en': {
        'Custom LOD Generator': 'Custom LOD Generator',
        'Number of LODs': 'Number of LODs',
        'Reduction Percentage:': 'Reduction Percentage:',
        'Delete Original': 'Delete Original',
        'Shift LODs': 'Shift LODs',
        'Shift Axis': 'Shift Axis',
        'Generate LODs': 'Generate LODs',
        'LOD{} Reduction (%)': 'LOD{} Reduction (%)',
        'LOD Naming Template': 'LOD Naming Template',
        'Use {original_name} and {index} as placeholders': 'Use {original_name} and {index} as placeholders',
        'LOD successfully generated': 'LOD successfully generated',
        'No objects selected for LOD generation': 'No objects selected for LOD generation',
        'X': 'X',
        'Y': 'Y',
        'Z': 'Z',
        'Language': 'Language',
    },
    'ru': {
        'Custom LOD Generator': 'Генератор LOD',
        'Number of LODs': 'Количество LOD',
        'Reduction Percentage:': 'Процент упрощения:',
        'Delete Original': 'Удалить оригинал',
        'Shift LODs': 'Смещать LOD',
        'Shift Axis': 'Ось смещения',
        'Generate LODs': 'Сгенерировать LODs',
        'LOD{} Reduction (%)': 'LOD{} Процент упрощения (%)',
        'LOD Naming Template': 'Шаблон именования LOD',
        'Use {original_name} and {index} as placeholders': 'Используйте {original_name} и {index} в качестве заменителей',
        'LOD successfully generated': 'LOD успешно сгенерированы',
        'No objects selected for LOD generation': 'Нет выбранных объектов для генерации LOD',
        'X': 'X',
        'Y': 'Y',
        'Z': 'Z',
        'Language': 'Язык',
    },
    'zh': {
        'Custom LOD Generator': '自定义LOD生成器',
        'Number of LODs': 'LOD数量',
        'Reduction Percentage:': '简化百分比：',
        'Delete Original': '删除原始对象',
        'Shift LODs': '移动LOD',
        'Shift Axis': '移动轴',
        'Generate LODs': '生成LOD',
        'LOD{} Reduction (%)': 'LOD{} 简化百分比 (%)',
        'LOD Naming Template': 'LOD命名模板',
        'Use {original_name} and {index} as placeholders': '使用{original_name}和{index}作为占位符',
        'LOD successfully generated': 'LOD成功生成',
        'No objects selected for LOD generation': '未选择对象生成LOD',
        'X': 'X',
        'Y': 'Y',
        'Z': 'Z',
        'Language': '语言',
    },
    'es': {
        'Custom LOD Generator': 'Generador de LOD Personalizado',
        'Number of LODs': 'Cantidad de LOD',
        'Reduction Percentage:': 'Porcentaje de reducción:',
        'Delete Original': 'Eliminar original',
        'Shift LODs': 'Desplazar LODs',
        'Shift Axis': 'Eje de desplazamiento',
        'Generate LODs': 'Generar LODs',
        'LOD{} Reduction (%)': 'LOD{} Porcentaje de reducción (%)',
        'LOD Naming Template': 'Plantilla de nombres LOD',
        'Use {original_name} and {index} as placeholders': 'Usa {original_name} e {index} como marcadores de posición',
        'LOD successfully generated': 'LOD generado con éxito',
        'No objects selected for LOD generation': 'No hay objetos seleccionados para generar LOD',
        'X': 'X',
        'Y': 'Y',
        'Z': 'Z',
        'Language': 'Idioma',
    },
}

def get_default_language():
    system_lang = locale.getdefaultlocale()[0]
    if system_lang:
        lang_code = system_lang.split('_')[0]
        if lang_code in translations:
            return lang_code
    return 'en'

class ReductionPercentageItem(PropertyGroup):
    value: FloatProperty(
        name="Reduction Percentage",
        default=50.0,
        min=0.0,
        max=99.0,  
        description="Процент сокращения полигонов"
    )

class LODSettings(PropertyGroup):
    def update_lod_count(self, context):
        settings = self
        
        while len(settings.reduction_percentages) < settings.lod_count:
            item = settings.reduction_percentages.add()
            item.value = 50.0  

        
        while len(settings.reduction_percentages) > settings.lod_count:
            settings.reduction_percentages.remove(len(settings.reduction_percentages)-1)

    def update_language(self, context):
        for area in context.window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

    def initialize(self):
        if len(self.reduction_percentages) < self.lod_count:
            self.update_lod_count(None)

    lod_count: IntProperty(
        name="Количество LOD",
        default=1,
        min=1,
        max=5,
        description="Количество уровней детализации",
        update=update_lod_count
    )
    reduction_percentages: CollectionProperty(
        type=ReductionPercentageItem,
        name="Проценты упрощения",
        description="Процент сокращения полигонов для каждого LOD"
    )
    delete_original: BoolProperty(
        name="Удалить оригинал",
        default=False,
        description="Удалить оригинальный объект после генерации LOD"
    )
    shift_lods: BoolProperty(
        name="Смещать LOD",
        default=True,
        description="Смещать LOD объекты, чтобы они не перекрывали друг друга"
    )
    shift_axis: EnumProperty(
        name="Ось смещения",
        items=[
            ('X', "X", "Смещение по оси X"),
            ('Y', "Y", "Смещение по оси Y"),
            ('Z', "Z", "Смещение по оси Z")
        ],
        default='X',
        description="Ось, по которой будут смещены LOD объекты"
    )
    language: EnumProperty(
        name="Язык",
        items=[
            ('en', 'English', ''),
            ('ru', 'Русский', ''),
            ('zh', '中文', ''),
            ('es', 'Español', ''),
        ],
        default=get_default_language(),
        update=update_language
    )
    naming_template: StringProperty(
        name="Шаблон именования LOD",
        default="{original_name}_LOD{index}",
        description="Шаблон для именования LOD объектов. Используйте {original_name} и {index} в качестве заменителей."
    )

def mesh_simplify(obj, target_face_count):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    current_face_count = len(bm.faces)

    if current_face_count <= target_face_count:
        bm.to_mesh(mesh)
        bm.free()
        return

    while len(bm.faces) > target_face_count:
        
        edges = sorted([e for e in bm.edges if e.is_valid], key=lambda e: e.calc_length())

        if not edges:
            break  

        edge = edges[0]  

        if not edge.is_valid:
            continue

        
        bmesh.ops.collapse(bm, edges=[edge])

    bm.to_mesh(mesh)
    bm.free()

class OBJECT_OT_generate_lods(Operator):
    bl_label = "Сгенерировать LODs"
    bl_idname = "object.generate_lods_custom"
    bl_description = "Генерирует LOD без использования модификатора Decimate"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.lod_settings

       
        def t(text):
            lang = settings.language
            return translations.get(lang, {}).get(text, text)

        
        settings.initialize()

        
        if len(settings.reduction_percentages) < settings.lod_count:
            settings.update_lod_count(context)

        
        objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not objects:
            self.report({'WARNING'}, t("No objects selected for LOD generation"))
            return {'CANCELLED'}

        for obj in objects:
            
            obj_collections = obj.users_collection

           
            if settings.shift_lods:
                
                obj_dimensions = obj.dimensions
                shift_distance = obj_dimensions[{'X': 0, 'Y': 1, 'Z': 2}[settings.shift_axis]] * 1.1
            else:
                shift_distance = 0

            
            for i in range(settings.lod_count):
                reduction_percentage = settings.reduction_percentages[i].value
                target_face_count = int(len(obj.data.polygons) * (1 - reduction_percentage / 100))
                target_face_count = max(target_face_count, 4)  

                lod = obj.copy()
                lod.data = obj.data.copy()

                
                naming_template = settings.naming_template
                lod_name = naming_template.format(original_name=obj.name, index=i)
                lod.name = lod_name

               
                for col in obj_collections:
                    col.objects.link(lod)

                
                mesh_simplify(lod, target_face_count)

                
                if settings.shift_lods:
                    offset = shift_distance * (i + 1)
                    if settings.shift_axis == 'X':
                        lod.location.x += offset
                    elif settings.shift_axis == 'Y':
                        lod.location.y += offset
                    elif settings.shift_axis == 'Z':
                        lod.location.z += offset

            
            if settings.delete_original:
                bpy.data.objects.remove(obj, do_unlink=True)

        self.report({'INFO'}, t("LOD successfully generated"))
        return {'FINISHED'}

class OBJECT_PT_lod_panel(Panel):
    bl_label = "Custom LOD Generator"
    bl_idname = "OBJECT_PT_lod_generator_custom"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LOD Generator'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.lod_settings

        
        settings.initialize()

        
        def t(text):
            lang = settings.language
            return translations.get(lang, {}).get(text, text)

        layout.prop(settings, "language", text=t("Language"))

        layout.prop(settings, "lod_count", text=t("Number of LODs"))

        col = layout.column(align=True)
        col.label(text=t("Reduction Percentage:"))

        for i in range(settings.lod_count):
            item = settings.reduction_percentages[i]
            col.prop(item, "value", text=t("LOD{} Reduction (%)").format(i))

        layout.prop(settings, "naming_template", text=t("LOD Naming Template"))
        layout.label(text=t("Use {original_name} and {index} as placeholders"))

        layout.prop(settings, "delete_original", text=t("Delete Original"))
        layout.prop(settings, "shift_lods", text=t("Shift LODs"))
        if settings.shift_lods:
            layout.prop(settings, "shift_axis", text=t("Shift Axis"))

        layout.operator("object.generate_lods_custom", text=t("Generate LODs"))

def register():
    bpy.utils.register_class(ReductionPercentageItem)
    bpy.utils.register_class(LODSettings)
    bpy.types.Scene.lod_settings = bpy.props.PointerProperty(type=LODSettings)

    bpy.utils.register_class(OBJECT_OT_generate_lods)
    bpy.utils.register_class(OBJECT_PT_lod_panel)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_generate_lods)
    bpy.utils.unregister_class(OBJECT_PT_lod_panel)
    bpy.utils.unregister_class(LODSettings)
    bpy.utils.unregister_class(ReductionPercentageItem)
    del bpy.types.Scene.lod_settings

if __name__ == "__main__":
    register()
