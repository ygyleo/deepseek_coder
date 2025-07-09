static bool ValidateTestPropertyName(const ::std::string& name)
    {
        const char* ban[] = {
            "name", "tests", "failures", "disabled", "skip", "errors", "time", "timestamp", "random_seed"
        };
#if !defined(IUTEST_NO_FUNCTION_TEMPLATE_ORDERING)
        return TestProperty::ValidateName(name, ban);
#else
        return TestProperty::ValidateName(name, ban, ban+IUTEST_PP_COUNTOF(ban));
#endif
    }
