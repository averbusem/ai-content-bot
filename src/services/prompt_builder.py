from typing import Optional, Dict, Any


def build_free_text_prompt(user_text: str, nko_data: Optional[Dict[str, Any]] = None) -> str:
    prompt_parts = []
    
    if nko_data:
        name = nko_data.get("name")
        if name:
            prompt_parts.append(f"Организация: {name}")
        
        activity = nko_data.get("activity")
        if activity:
            prompt_parts.append(f"Деятельность: {activity}")
        
        forms = nko_data.get("forms", [])
        if forms:
            forms_list = []
            for form_key in forms:
                if form_key == "other":
                    other_text = nko_data.get("forms_other", "")
                    if other_text:
                        forms_list.append(other_text)
                else:
                    forms_list.append(form_key)
            if forms_list:
                prompt_parts.append(f"Формы деятельности: {', '.join(forms_list)}")
        
        region = nko_data.get("region")
        if region:
            prompt_parts.append(f"Регион работы: {region}")
    
    prompt_parts.append(f"\nЗапрос пользователя: {user_text}")
    print("\n".join(prompt_parts))
    return "\n".join(prompt_parts)


