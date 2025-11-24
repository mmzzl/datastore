from rest_framework import serializers
from .models import Category, QuestionCategory
import structlog

logger = structlog.get_logger(__name__)


class CategorySerializer(serializers.ModelSerializer):
    """分类序列化器"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    children_count = serializers.IntegerField(source='get_children_count', read_only=True)
    questions_count = serializers.IntegerField(source='get_questions_count', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = Category
        fields = (
            'id', 'user', 'name', 'description', 'color', 'icon', 'parent', 'parent_name',
            'level', 'sort_order', 'is_system', 'is_active', 'created_at', 'updated_at',
            'children_count', 'questions_count', 'full_name'
        )
        read_only_fields = ('id', 'user', 'level', 'created_at', 'updated_at', 'children_count', 'questions_count', 'full_name')


class CategoryBatchCreateSerializer(serializers.Serializer):
    """批量创建分类序列化器"""
    categories = serializers.ListField(
        child=serializers.JSONField(),
        write_only=True,
        help_text="分类列表，每个分类包含name和parent_id(可选)"
    )
    
    def validate_categories(self, value):
        """验证分类列表"""
        if not value:
            raise serializers.ValidationError("分类列表不能为空")
        
        if len(value) > 50:
            raise serializers.ValidationError("一次最多创建50个分类")
        
        # 验证每个分类的基本信息
        for i, category in enumerate(value):
            if not isinstance(category, dict):
                raise serializers.ValidationError(f"第{i+1}个分类必须是对象格式")
            
            if 'name' not in category:
                raise serializers.ValidationError(f"第{i+1}个分类缺少name字段")
            
            name = category['name']
            if not isinstance(name, str) or not name.strip():
                raise serializers.ValidationError(f"第{i+1}个分类的name不能为空")
            
            if len(name) > 50:
                raise serializers.ValidationError(f"第{i+1}个分类的name长度不能超过50个字符")
        
        return value
    
    def create(self, validated_data):
        """批量创建分类"""
        categories_data = validated_data['categories']
        user = self.context['request'].user
        created_categories = []
        
        # 先创建所有分类（不设置parent关系）
        for category_data in categories_data:
            name = category_data['name'].strip()
            description = category_data.get('description', '')
            color = category_data.get('color', '#1890ff')
            
            category = Category.objects.create(
                name=name,
                description=description,
                color=color,
                user=user
            )
            created_categories.append(category)
        
        # 然后设置parent关系
        for i, category_data in enumerate(categories_data):
            if 'parent_id' in category_data and category_data['parent_id']:
                parent_id = category_data['parent_id']
                # 查找对应的父分类
                for j, parent_data in enumerate(categories_data):
                    if parent_data.get('temp_id') == parent_id:
                        created_categories[i].parent = created_categories[j]
                        created_categories[i].save()
                        break
        
        return created_categories


class CategoryTreeSerializer(serializers.ModelSerializer):
    """分类树形结构序列化器"""
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'color', 'icon', 'level', 'sort_order', 'is_system', 'children')
    
    def get_children(self, obj):
        children = obj.children.filter(is_active=True).order_by('sort_order', 'id')
        return CategoryTreeSerializer(children, many=True).data


class QuestionCategorySerializer(serializers.ModelSerializer):
    """错题分类关联序列化器"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)
    
    class Meta:
        model = QuestionCategory
        fields = ('id', 'question', 'category', 'category_name', 'category_color', 'category_icon', 'created_at')
        read_only_fields = ('id', 'created_at')


class CategoryCreateSerializer(serializers.ModelSerializer):
    """分类创建序列化器"""
    
    class Meta:
        model = Category
        fields = (
            'name', 'description', 'color', 'icon', 'parent', 'sort_order', 'is_active'
        )
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        
        # 如果有父分类，设置层级
        parent = validated_data.get('parent')
        if parent:
            validated_data['level'] = parent.level + 1
        else:
            validated_data['level'] = 1
        
        category = Category.objects.create(**validated_data)
        
        logger.info("创建分类成功", category_id=category.id, user_id=user.id)
        return category


class CategoryUpdateSerializer(serializers.ModelSerializer):
    """分类更新序列化器"""
    
    class Meta:
        model = Category
        fields = (
            'name', 'description', 'color', 'icon', 'parent', 'sort_order', 'is_active'
        )
    
    def update(self, instance, validated_data):
        # 如果父分类发生变化，需要更新层级
        parent = validated_data.get('parent')
        if parent and parent != instance.parent:
            validated_data['level'] = parent.level + 1
        elif not parent and instance.parent:
            validated_data['level'] = 1
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        logger.info("更新分类成功", category_id=instance.id, user_id=instance.user.id)
        return instance


class QuestionCategoryCreateSerializer(serializers.ModelSerializer):
    """错题分类关联创建序列化器"""
    
    class Meta:
        model = QuestionCategory
        fields = ('question', 'category')
    
    def create(self, validated_data):
        question_category = QuestionCategory.objects.create(**validated_data)
        
        logger.info(
            "创建错题分类关联成功",
            question_id=question_category.question.id,
            category_id=question_category.category.id
        )
        return question_category