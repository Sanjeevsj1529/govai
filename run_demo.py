from baseline import compare_policies, print_summary


if __name__ == "__main__":
    print_summary(compare_policies(mode="medium", seed=7))
